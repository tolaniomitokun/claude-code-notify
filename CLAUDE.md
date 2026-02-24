# Claude Code Notify — Project Context

## What This Is
A notification system for Claude Code that alerts you on your Mac and phone when Claude needs attention. Built as an open-source project at https://github.com/tolaniomitokun/claude-code-notify.

## Architecture

### Notification Channels (3 channels, all optional)
1. **macOS notification** — native notification with sound, always fires
2. **Telegram bot** — push notification from a bot named "Claude Code" (bot token: stored in `.env`)
3. **iMessage** — sends to your own phone number (shows as sent-to-yourself, works but Telegram is cleaner)

### Smart Notifications
- Tracks user activity via `activity-tracker.sh` on every `UserPromptSubmit` event
- Writes timestamp to `~/.claude/notify/last_activity`
- `claude-notify.sh` checks: if user was active < 2 min ago, only macOS notification fires (no phone spam)
- If idle > 2 min, all channels fire
- Threshold configurable via `IDLE_THRESHOLD` in `.env`

### Telegram Action Buttons
- `telegram-permission.py` hooks into `PermissionRequest` event
- Sends Telegram message with inline Allow/Deny buttons
- Two threads race: Telegram callback polling vs Unix socket (Barbara's dashboard)
- Whichever responds first wins, message updates to show result
- Uses `curl` via `subprocess` for Telegram API (avoids Python SSL issues on macOS)

### Session Summary + Cost Tracker
- `session-summary.sh` hooks into `SessionEnd` event
- Reads session metrics from `~/.claude/notify/sessions/{SESSION_ID}.json`
- Also reads Barbara's session data from `~/.claude/monitor/sessions/{SESSION_ID}.json`
- Sends Telegram recap: duration, prompt count, estimated cost
- Cost = prompt_count × `COST_PER_PROMPT` (default $0.165 for Opus)
- Cleans up metrics file after sending

## Files

| File | Purpose |
|------|---------|
| `claude-notify.sh` | Main notification hook — macOS + Telegram + iMessage with smart idle check |
| `activity-tracker.sh` | UserPromptSubmit hook — tracks activity timestamps and per-session metrics |
| `session-summary.sh` | SessionEnd hook — sends Telegram recap with duration, prompts, cost |
| `telegram-permission.py` | PermissionRequest hook — Telegram Allow/Deny buttons + Unix socket for dashboard |
| `.env` | Secrets: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PHONE_NUMBER, IDLE_THRESHOLD, COST_PER_PROMPT |
| `.env.example` | Template for `.env` |

## Data Directories

| Path | Purpose |
|------|---------|
| `~/.claude/notify/last_activity` | Unix timestamp of last user prompt (for smart notifications) |
| `~/.claude/notify/sessions/{ID}.json` | Per-session metrics: prompt_count, started_at, project, model |
| `~/.claude/monitor/sessions/{ID}.json` | Barbara's session data: status, project, cwd, timestamps (read-only) |

## Hook Configuration (`~/.claude/settings.json`)

```
UserPromptSubmit → activity-tracker.sh (tracks activity + session metrics)
Notification     → claude-notify.sh (sends macOS/Telegram/iMessage alerts)
PermissionRequest → telegram-permission.py (Telegram buttons + Unix socket)
SessionEnd       → session-summary.sh (Telegram recap)
```

Barbara's hooks also registered: SessionStart, UserPromptSubmit, Stop, Notification, PermissionRequest (Unix socket), SessionEnd — all via `monitor.sh` and `monitor_permission.py`.

## Integration with Barbara's Claude Monitor
- Repo: https://github.com/brb-dreaming/claude-monitor
- Cloned locally at `/Users/tolaniomitokun/claude-monitor`
- Installed to `~/.claude/monitor/` (Swift dashboard, build.sh, config.json)
- Hooks at `~/.claude/hooks/monitor.sh` and `~/.claude/hooks/monitor_permission.py`
- `telegram-permission.py` replaces `monitor_permission.py` in settings.json but preserves all its functionality (writes .permission file, connects to Unix socket)
- Both the floating dashboard and Telegram buttons work simultaneously — first response wins

## Known Issues
- **macOS notifications**: May not show if terminal app (iTerm) notifications are disabled in System Settings
- **iMessage**: Messages appear as sent-to-yourself (sender + receiver). No way around this.
- **Python SSL**: Python 3.12 from python.org has SSL cert issues on macOS. All Telegram API calls use `curl` via subprocess to avoid this.
- **Hooks only load at session start**: Existing Claude Code sessions won't pick up new hooks until restarted. Type `/hooks` in a running session as a workaround.

## Credentials (local only, never committed)
- Telegram bot token and chat ID in `~/claude-code-notify/.env`
- Phone number for iMessage in `~/claude-code-notify/.env`
- `.env` is in `.gitignore`

## Inspiration
Inspired by Barbara's claude-monitor project (https://github.com/brb-dreaming/claude-monitor) which provides a floating macOS dashboard with voice announcements and permission granting.
