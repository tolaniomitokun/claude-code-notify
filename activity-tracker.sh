#!/bin/bash

# Activity Tracker for Claude Code
# Hook for UserPromptSubmit: tracks user activity and session metrics
# https://github.com/tolaniomitokun/claude-code-notify

DATA_DIR="$HOME/.claude/notify"
SESSIONS_DIR="$DATA_DIR/sessions"
ACTIVITY_FILE="$DATA_DIR/last_activity"

mkdir -p "$SESSIONS_DIR"

# Read hook input from stdin
INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)
CWD=$(echo "$INPUT" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)

NOW=$(date +%s)

# 1. Update global last-activity timestamp (for smart notifications)
echo "$NOW" > "$ACTIVITY_FILE"

# 2. Update per-session metrics
if [ -n "$SESSION_ID" ]; then
    METRICS_FILE="$SESSIONS_DIR/${SESSION_ID}.json"

    if [ -f "$METRICS_FILE" ]; then
        # Increment prompt_count
        /usr/bin/python3 -c "
import json, time
with open('$METRICS_FILE') as f:
    data = json.load(f)
data['prompt_count'] = data.get('prompt_count', 0) + 1
data['last_activity'] = int(time.time())
with open('$METRICS_FILE', 'w') as f:
    json.dump(data, f)
"
    else
        # Create initial metrics file
        PROJECT=$(basename "${CWD:-unknown}")
        if [ "$CWD" = "$HOME" ] || [ -z "$CWD" ]; then
            PROJECT="Home"
        fi
        /usr/bin/python3 -c "
import json, time
data = {
    'session_id': '$SESSION_ID',
    'project': '$PROJECT',
    'started_at': int(time.time()),
    'prompt_count': 1,
    'last_activity': int(time.time()),
    'model': 'opus'
}
with open('$METRICS_FILE', 'w') as f:
    json.dump(data, f)
"
    fi
fi

exit 0
