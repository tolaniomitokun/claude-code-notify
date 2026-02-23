#!/bin/bash

# Claude Code Notification Hook
# Sends a macOS notification + Telegram message + iMessage when Claude needs attention
# https://github.com/tolaniomitokun/claude-code-notify

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
fi

# Read hook input from stdin
INPUT=$(cat)

# Parse fields from hook JSON
parse() { echo "$INPUT" | /usr/bin/python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$1',''))" 2>/dev/null; }

MESSAGE=$(parse message)
CWD=$(parse cwd)
NOTIFICATION_TYPE=$(parse notification_type)

# Extract project name from working directory
PROJECT=$(basename "${CWD:-unknown}")

# Customize message based on notification type
case "$NOTIFICATION_TYPE" in
  permission_prompt)
    EMOJI="🔐"
    LABEL="Permission Needed"
    SOUND="Glass"
    ;;
  idle_prompt)
    EMOJI="✅"
    LABEL="Task Complete"
    MESSAGE="Claude finished working and is ready for your next prompt."
    SOUND="Hero"
    ;;
  *)
    EMOJI="🤖"
    LABEL="Attention"
    SOUND="Glass"
    ;;
esac

# Fallback
MESSAGE=${MESSAGE:-"Claude Code needs your attention"}

# 1. macOS notification with sound
osascript -e "display notification \"${MESSAGE}\" with title \"Claude Code — ${LABEL}\" subtitle \"${PROJECT}\" sound name \"${SOUND}\""

# 2. Telegram message to phone
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
  TELEGRAM_MSG="${EMOJI} *Claude Code — ${PROJECT}*
${LABEL}: ${MESSAGE}"
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "parse_mode=Markdown" \
    --data-urlencode "text=${TELEGRAM_MSG}" > /dev/null 2>&1
fi

# 3. iMessage to phone (macOS only)
if [ -n "$PHONE_NUMBER" ]; then
  IMESSAGE="${EMOJI} Claude Code — ${PROJECT}
${LABEL}: ${MESSAGE}"
  osascript -e "tell application \"Messages\" to send \"${IMESSAGE}\" to buddy \"${PHONE_NUMBER}\""
fi

exit 0
