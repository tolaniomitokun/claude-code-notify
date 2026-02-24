#!/usr/bin/env python3
"""
Combined PermissionRequest handler for Claude Code.
- Sends Telegram message with inline Allow/Deny buttons
- Listens on Unix socket for Barbara's dashboard response
- Whichever responds first wins
https://github.com/tolaniomitokun/claude-code-notify
"""

import json
import socket
import sys
import os
import time
import threading
import urllib.request
import urllib.parse
import urllib.error

SOCKET_PATH = "/tmp/claude-monitor.sock"
TIMEOUT_SECONDS = 300  # 5 min max wait


def load_env():
    """Load .env file from script directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ[key.strip()] = value.strip()


def send_telegram_permission(bot_token, chat_id, session_id, tool_name, display):
    """Send Telegram message with inline Allow/Deny buttons."""
    keyboard = json.dumps({
        "inline_keyboard": [
            [
                {"text": "Allow", "callback_data": f"perm_allow_{session_id}"},
                {"text": "Deny", "callback_data": f"perm_deny_{session_id}"},
            ]
        ]
    })

    text = (
        f"🔐 *Permission Request*\n\n"
        f"Tool: `{tool_name}`\n"
        f"```\n{display}\n```"
    )

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": keyboard,
    }).encode()

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        req = urllib.request.Request(url, data=data)
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result.get("result", {}).get("message_id")
    except Exception:
        return None


def answer_callback(bot_token, callback_id, text):
    """Answer a Telegram callback query (removes loading spinner)."""
    try:
        data = urllib.parse.urlencode({
            "callback_query_id": callback_id,
            "text": text,
        }).encode()
        url = f"https://api.telegram.org/bot{bot_token}/answerCallbackQuery"
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=5)
    except Exception:
        pass


def update_telegram_message(bot_token, chat_id, message_id, decision):
    """Edit the original message to show the decision result."""
    if decision == "allow":
        text = "🔐 Permission Request\n\nResult: ✅ Allowed"
    else:
        text = "🔐 Permission Request\n\nResult: ❌ Denied"
    try:
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode()
        url = f"https://api.telegram.org/bot{bot_token}/editMessageText"
        urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=5)
    except Exception:
        pass


def poll_telegram(bot_token, chat_id, session_id, result_holder, stop_event):
    """Poll Telegram for callback query responses (button presses)."""
    last_update_id = 0

    # Get current update_id to skip old callbacks
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates?offset=-1&limit=1"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data.get("result"):
            last_update_id = data["result"][-1]["update_id"] + 1
    except Exception:
        pass

    while not stop_event.is_set():
        try:
            url = (
                f"https://api.telegram.org/bot{bot_token}/getUpdates"
                f"?offset={last_update_id}&timeout=5"
                f"&allowed_updates=%5B%22callback_query%22%5D"
            )
            resp = urllib.request.urlopen(url, timeout=15)
            data = json.loads(resp.read())

            for update in data.get("result", []):
                last_update_id = update["update_id"] + 1
                cb = update.get("callback_query")
                if not cb:
                    continue

                cb_data = cb.get("data", "")
                cb_id = cb.get("id")
                msg = cb.get("message", {})

                if cb_data == f"perm_allow_{session_id}":
                    answer_callback(bot_token, cb_id, "Allowed")
                    update_telegram_message(
                        bot_token, chat_id, msg.get("message_id"), "allow"
                    )
                    result_holder["decision"] = "allow"
                    stop_event.set()
                    return
                elif cb_data == f"perm_deny_{session_id}":
                    answer_callback(bot_token, cb_id, "Denied")
                    update_telegram_message(
                        bot_token, chat_id, msg.get("message_id"), "deny"
                    )
                    result_holder["decision"] = "deny"
                    stop_event.set()
                    return

        except Exception:
            if not stop_event.is_set():
                time.sleep(2)


def listen_socket(session_id, tool_name, display, tool_input_str,
                  result_holder, stop_event):
    """Connect to Unix socket for Barbara's dashboard response."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect(SOCKET_PATH)
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        return  # Dashboard not running

    request = {
        "type": "permission_request",
        "session_id": session_id,
        "tool_name": tool_name,
        "display": display,
        "tool_input": tool_input_str,
    }
    try:
        sock.sendall(json.dumps(request).encode())
    except Exception:
        sock.close()
        return

    # Wait for response
    try:
        while not stop_event.is_set():
            sock.settimeout(1.0)
            try:
                response_data = sock.recv(4096)
                if response_data:
                    response = json.loads(response_data.decode())
                    decision = response.get("decision", "")
                    if decision in ("allow", "deny", "terminal"):
                        result_holder["decision"] = decision
                        stop_event.set()
                    return
            except socket.timeout:
                continue
    except Exception:
        pass
    finally:
        sock.close()


def cleanup(perm_file):
    try:
        os.remove(perm_file)
    except FileNotFoundError:
        pass


def main():
    input_data = json.loads(sys.stdin.read())

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    session_id = input_data.get("session_id", "")

    # Build display text (same logic as monitor_permission.py)
    if tool_name == "Bash":
        display = tool_input.get("command", "")[:300]
    elif tool_name in ("Edit", "Write", "Read"):
        display = tool_input.get("file_path", "")
    else:
        display = json.dumps(tool_input)[:300]

    # Write .permission file for Barbara's dashboard UI
    sessions_dir = os.path.expanduser("~/.claude/monitor/sessions")
    perm_file = os.path.join(sessions_dir, f"{session_id}.permission")
    perm_data = {
        "tool_name": tool_name,
        "display": display,
        "tool_input": json.dumps(tool_input),
        "timestamp": input_data.get("hook_event_name", ""),
    }
    try:
        os.makedirs(sessions_dir, exist_ok=True)
        tmp_file = perm_file + ".tmp"
        with open(tmp_file, "w") as f:
            json.dump(perm_data, f)
        os.replace(tmp_file, perm_file)
    except Exception:
        pass

    # Load environment
    load_env()
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    # Shared state between threads
    result_holder = {"decision": None}
    stop_event = threading.Event()

    # Send Telegram message with buttons
    msg_id = None
    if bot_token and chat_id:
        msg_id = send_telegram_permission(
            bot_token, chat_id, session_id, tool_name, display
        )

    # Start competing listeners
    # Thread 1: Unix socket (Barbara's dashboard)
    t1 = threading.Thread(
        target=listen_socket,
        args=(session_id, tool_name, display, json.dumps(tool_input),
              result_holder, stop_event),
        daemon=True,
    )
    t1.start()

    # Thread 2: Telegram polling
    if bot_token and chat_id and msg_id:
        t2 = threading.Thread(
            target=poll_telegram,
            args=(bot_token, chat_id, session_id, result_holder, stop_event),
            daemon=True,
        )
        t2.start()

    # Wait for either to respond
    stop_event.wait(timeout=TIMEOUT_SECONDS)

    # Cleanup
    cleanup(perm_file)

    decision = result_holder.get("decision")

    if decision == "allow":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {"behavior": "allow"},
            }
        }
        print(json.dumps(output))
    elif decision == "deny":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": {
                    "behavior": "deny",
                    "message": "Denied from remote",
                },
            }
        }
        print(json.dumps(output))
    # else: terminal or timeout — exit with no output, falls through to terminal dialog


if __name__ == "__main__":
    main()
