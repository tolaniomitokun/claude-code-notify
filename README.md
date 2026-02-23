# Claude Code Notify

Get notified on your Mac and phone when [Claude Code](https://docs.anthropic.com/en/docs/claude-code) needs your attention.

Stop staring at your terminal waiting. Step away, grab coffee, go for a walk — you'll get a ping the moment Claude needs you.

## What It Does

When Claude Code is working on your project, there are moments where it pauses and waits for you — like when it needs permission to run a command, or when it finishes a task. Normally, you'd have to keep watching the terminal to notice.

**This project sends you a notification instantly** through up to three channels:

| Channel | Where | Best For |
|---------|-------|----------|
| **macOS notification** | Your Mac screen + sound | When you're at your desk but in another app |
| **Telegram bot** | Your phone (iOS/Android) | When you're away from your desk |
| **iMessage** | Your iPhone/iPad/Apple Watch | If you prefer iMessage over Telegram |

Each notification tells you **which project** and **what Claude needs**:

```
🔐 Claude Code — my-saas-app
Permission Needed: Claude needs your permission to use Bash

✅ Claude Code — my-saas-app
Task Complete: Claude finished working and is ready for your next prompt.
```

## What You'll Need

Before starting, make sure you have:

- **A Mac** — this project uses macOS-specific features (notifications, iMessage)
- **Claude Code** — Anthropic's CLI tool. [Install it here](https://docs.anthropic.com/en/docs/claude-code) if you haven't already
- **Telegram** (optional) — install the app on your [iPhone](https://apps.apple.com/app/telegram-messenger/id686449807) or [Android](https://play.google.com/store/apps/details?id=org.telegram.messenger) phone for phone notifications
- **`curl` and `python3`** — these come pre-installed on every Mac, so you likely already have them

## Setup (5 minutes)

### Step 1: Download the project

Open your terminal (search for "Terminal" in Spotlight, or find it in Applications → Utilities) and paste this:

```bash
git clone https://github.com/tolaniomitokun/claude-code-notify.git ~/claude-code-notify
cd ~/claude-code-notify
chmod +x claude-notify.sh
```

**What this does:** Downloads the project to your home folder and makes the script executable.

### Step 2: Set up your notification channels

You can set up one, two, or all three. Each channel is independent.

---

#### Option A: Telegram bot (recommended for phone notifications)

This creates a Telegram bot named "Claude Code" that sends you messages. It takes about 2 minutes.

**On your phone:**

1. Open the **Telegram** app
2. Search for **@BotFather** (this is Telegram's official tool for creating bots)
3. Tap **Start**, then type `/newbot`
4. BotFather will ask for a display name — type: `Claude Code`
5. BotFather will ask for a username — pick something unique like `claude_code_yourname_bot` (must end in `bot`)
6. BotFather will reply with an **API token** — it looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`. Copy this, you'll need it soon
7. Now search for your new bot by the username you just picked
8. Open the chat and tap **Start** (this is important — the bot can't message you until you do this)

**Back on your Mac terminal:**

Get your chat ID by running this (replace `YOUR_TOKEN` with the API token from step 6):

```bash
curl -s https://api.telegram.org/botYOUR_TOKEN/getUpdates | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['result']:
    print('Your chat ID is:', data['result'][0]['message']['chat']['id'])
else:
    print('No messages found. Make sure you sent /start to your bot first.')
"
```

Save both the **API token** and **chat ID** — you'll enter them in Step 3.

---

#### Option B: iMessage

No setup needed — you just need to know the phone number or email tied to your iMessage account.

> **Heads up:** iMessage sends from your own Apple ID to yourself, so each message appears twice (once as sent, once as received). It works fine for notifications, but Telegram looks cleaner. Many people set up both and decide later which they prefer.

---

#### Option C: macOS notifications only

No setup needed at all. This is always on by default.

**Tip:** Go to **System Settings → Notifications** → find your terminal app (Terminal or iTerm) → set the notification style to **Alerts** instead of Banners. Alerts stay on screen until you dismiss them, so you won't miss a notification.

---

### Step 3: Add your settings

In your terminal, run:

```bash
cp .env.example .env
```

Now open the `.env` file in any text editor and fill in your values:

```bash
# Your Telegram bot token (from BotFather — leave blank to skip Telegram)
TELEGRAM_BOT_TOKEN=

# Your Telegram chat ID (from the curl command above — leave blank to skip Telegram)
TELEGRAM_CHAT_ID=

# Your phone number for iMessage (e.g. +1234567890 — leave blank to skip iMessage)
PHONE_NUMBER=
```

**Only fill in what you want to use.** Leave a line blank to disable that channel.

> **Security note:** The `.env` file stays on your machine only. It's in `.gitignore` so it will never be uploaded to GitHub, even if you fork or contribute to this project.

### Step 4: Connect it to Claude Code

You need to tell Claude Code to run this script when notifications happen.

Open (or create) the file `~/.claude/settings.json` and add the hooks configuration. If the file already has content, merge the `hooks` section into it:

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

**Alternatively**, you can type `/hooks` inside a Claude Code session to add it interactively without editing JSON.

### Step 5: Test it

Run this in your terminal to simulate a notification:

```bash
echo '{"message":"Claude needs your permission to use Bash","notification_type":"permission_prompt","cwd":"'$HOME'/my-project"}' | ~/claude-code-notify/claude-notify.sh
```

You should receive:
- A macOS notification with a "Glass" sound
- A Telegram message (if configured)
- An iMessage (if configured)

If something doesn't work, check the [Troubleshooting](#troubleshooting) section below.

## Notification Types

The script sends different notifications depending on what's happening:

| Icon | Type | When it fires | Mac sound | Message |
|------|------|---------------|-----------|---------|
| 🔐 | **Permission Needed** | Claude wants to run a command and needs your approval | Glass | "Claude needs your permission to use [tool name]" |
| ✅ | **Task Complete** | Claude finished working and is waiting for your next instruction | Hero | "Claude finished working and is ready for your next prompt." |
| 🤖 | **Attention** | Any other notification from Claude Code | Glass | Varies |

## Customization

### Only get notified for specific events

If you only want phone notifications for permission prompts (not task completions), change the `matcher` in your `~/.claude/settings.json`:

```json
{
  "matcher": "permission_prompt",
  "hooks": [
    {
      "type": "command",
      "command": "~/claude-code-notify/claude-notify.sh"
    }
  ]
}
```

Valid matchers: `permission_prompt`, `idle_prompt`

### Disable a notification channel

Edit your `.env` file and remove the value for any channel you want to turn off:

- **Turn off Telegram** — delete the `TELEGRAM_BOT_TOKEN` value
- **Turn off iMessage** — delete the `PHONE_NUMBER` value
- **macOS notifications** are always on (they're local and free)

### Disable all notifications temporarily

Add this to your `~/.claude/settings.json`:

```json
{
  "disableAllHooks": true
}
```

Remove it (or set to `false`) to re-enable.

## Troubleshooting

### macOS notification not showing up

1. Go to **System Settings → Notifications**
2. Find your terminal app (**Terminal** or **iTerm**)
3. Make sure **Allow Notifications** is turned on
4. Set notification style to **Alerts** (stays on screen) instead of **Banners** (disappears after a few seconds)

### Telegram message not arriving

1. Make sure you opened a chat with your bot and sent `/start`
2. Double-check your `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
3. Test the bot directly:
   ```bash
   source ~/claude-code-notify/.env
   curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     -d "chat_id=${TELEGRAM_CHAT_ID}" \
     --data-urlencode "text=Test message from Claude Code"
   ```
   If this prints `"ok":true`, your bot is working. If not, re-check your token and chat ID.

### iMessage not arriving on phone

- iMessage sends from your own Apple ID to yourself. The message **will** appear in the Messages app on your Mac, but your iPhone may not alert you (since it's a message from yourself).
- Check **Settings → Messages → Send & Receive** on your iPhone and make sure your phone number is checked.
- Consider using Telegram instead for more reliable phone notifications.

### "permission denied" error when running the script

Run this to make the script executable:
```bash
chmod +x ~/claude-code-notify/claude-notify.sh
```

### macOS asks for permission to control Messages

This is a one-time macOS security prompt. Click **Allow** when you see it. If you accidentally denied it, go to **System Settings → Privacy & Security → Automation** and enable it for your terminal app.

## How It Works (Technical Details)

Claude Code has a [hooks system](https://docs.anthropic.com/en/docs/claude-code/hooks) that runs shell commands in response to lifecycle events. This project uses the `Notification` hook event, which fires whenever Claude Code needs the user's attention.

When the hook fires, Claude Code pipes a JSON object to the script via stdin:

```json
{
  "session_id": "abc123",
  "cwd": "/Users/you/your-project",
  "hook_event_name": "Notification",
  "notification_type": "permission_prompt",
  "message": "Claude needs your permission to use Bash",
  "title": "Claude Code"
}
```

The script parses this JSON, extracts the project name from `cwd`, determines the notification type, and sends alerts through each configured channel.

## Project Structure

```
claude-code-notify/
├── claude-notify.sh    # The hook script (this does all the work)
├── .env.example        # Template for your personal settings
├── .env                # Your actual settings (git-ignored, never uploaded)
├── .gitignore          # Keeps .env and other private files out of git
├── LICENSE             # MIT license
└── README.md           # This file
```

## Contributing

Found a bug or want to add a feature? PRs are welcome.

Some ideas:
- Slack/Discord webhook support
- Sound customization
- Notification filtering by project
- Linux support (libnotify)

## License

[MIT](LICENSE) — use it however you want.
