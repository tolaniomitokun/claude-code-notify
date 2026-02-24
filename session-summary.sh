#!/bin/bash

# Session Summary for Claude Code
# Hook for SessionEnd: sends a Telegram recap with duration, prompts, and estimated cost
# https://github.com/tolaniomitokun/claude-code-notify

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Read hook input from stdin
INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)

# Need session ID and Telegram configured
if [ -z "$SESSION_ID" ] || [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
  exit 0
fi

METRICS_FILE="$HOME/.claude/notify/sessions/${SESSION_ID}.json"

# No metrics tracked for this session
if [ ! -f "$METRICS_FILE" ]; then
  exit 0
fi

# Build and send summary
SUMMARY=$(/usr/bin/python3 - "$SESSION_ID" << 'PYEOF'
import json, time, os, sys

session_id = sys.argv[1] if len(sys.argv) > 1 else ""
metrics_file = os.path.expanduser(f"~/.claude/notify/sessions/{session_id}.json")
monitor_file = os.path.expanduser(f"~/.claude/monitor/sessions/{session_id}.json")
cost_per_prompt = float(os.environ.get("COST_PER_PROMPT", "0.165"))

metrics = {}
monitor = {}

if os.path.exists(metrics_file):
    with open(metrics_file) as f:
        metrics = json.load(f)

if os.path.exists(monitor_file):
    with open(monitor_file) as f:
        monitor = json.load(f)

project = metrics.get("project") or monitor.get("project", "Unknown")
prompt_count = metrics.get("prompt_count", 0)
started = metrics.get("started_at", 0)
now = int(time.time())
duration_secs = now - started if started else 0

# Format duration
hours = duration_secs // 3600
minutes = (duration_secs % 3600) // 60
if hours > 0:
    duration_str = f"{hours}h {minutes}m"
elif minutes > 0:
    duration_str = f"{minutes}m"
else:
    duration_str = "<1m"

cost = prompt_count * cost_per_prompt

print(f"\U0001f4ca *Session Summary \u2014 {project}*")
print()
print(f"\u23f1 Duration: {duration_str}")
print(f"\U0001f4ac Prompts: {prompt_count}")
print(f"\U0001f4b0 Est. Cost: ${cost:.2f}")
PYEOF
)

# Send via Telegram
if [ -n "$SUMMARY" ]; then
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "parse_mode=Markdown" \
    --data-urlencode "text=${SUMMARY}" > /dev/null 2>&1
fi

# Clean up metrics file
rm -f "$METRICS_FILE"

exit 0
