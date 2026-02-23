# Claude Code Notify

Get notified on your Mac and phone when [Claude Code](https://docs.anthropic.com/en/docs/claude-code) needs your attention.

Step away from your desk, grab coffee, and never miss a permission prompt or task completion again.

## How It Works

Claude Code has a [hooks system](https://docs.anthropic.com/en/docs/claude-code/hooks) that fires events during its lifecycle. This project hooks into the `Notification` event and sends alerts through three channels:

1. **macOS notification** — native notification with sound (different sounds per event type)
2. **Telegram bot** — push notification from a bot named "Claude Code"
3. **iMessage** — text message to your phone

Each notification includes the **project name** and **context** about what Claude needs:

```
🔐 Claude Code — my-saas-app
Permission Needed: Claude needs your permission to use Bash

✅ Claude Code — my-saas-app
Task Complete: Claude finished working and is ready for your next prompt.
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/tolaniomitokun/claude-code-notify.git ~/claude-code-notify
cd ~/claude-code-notify
chmod +x claude-notify.sh
```

### 2. Set up Telegram bot (optional)

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts — name it **Claude Code**
3. Copy the API token BotFather gives you
4. Open a chat with your new bot and send `/start`
5. Get your chat ID:
   ```bash
   curl -s https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['message']['chat']['id'])"
   ```

### 3. Set up iMessage (optional, macOS only)

No setup needed — just know the phone number or Apple ID email tied to your iMessage account.

> **Note:** iMessage sends from your own Apple ID, so messages appear as sent-to-yourself. It works, but you'll see both sent and received. Telegram is cleaner for phone notifications.

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
PHONE_NUMBER=+1234567890
```

Leave any value blank to disable that channel. Telegram and iMessage are both optional — use one, both, or neither.

### 5. Add the hook to Claude Code

Add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/claude-code-notify/claude-notify.sh"
          }
        ]
      }
    ]
  }
}
```

Or type `/hooks` inside Claude Code to add it interactively.

### 6. Test it

```bash
echo '{"message":"Claude needs your permission to use Bash","notification_type":"permission_prompt","cwd":"/Users/you/my-project"}' | ~/claude-code-notify/claude-notify.sh
```

## Notification Types

| Type | Trigger | Sound | Example |
|------|---------|-------|---------|
| 🔐 Permission Needed | Claude needs approval to run a tool | Glass | "Claude needs your permission to use Fetch" |
| ✅ Task Complete | Claude finished and is waiting for you | Hero | "Claude finished working and is ready for your next prompt." |
| 🤖 Attention | Any other notification | Glass | Generic attention message |

## Disabling Channels

Each channel is independent. To disable one:

- **Telegram** — remove `TELEGRAM_BOT_TOKEN` from `.env`
- **iMessage** — remove `PHONE_NUMBER` from `.env`
- **macOS notification** — always on (it's a local notification with no config needed)
- **All notifications** — add `"disableAllHooks": true` to your Claude Code settings

## Requirements

- macOS
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- Telegram app (for Telegram notifications)
- `curl` and `python3` (pre-installed on macOS)

## License

MIT
