# Deployment without Docker (Linux + systemd)

## 1. Server Requirements

- Ubuntu 22.04+ / Debian 12+ (or any Linux with systemd)
- Python 3.11+
- sqlite3 (usually pre-installed)
- Internet access (Telegram API, OpenAI API)

## 2. Server Setup

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Python and tools
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Create a dedicated user for the bot
sudo useradd -m -s /bin/bash tgbot
sudo su - tgbot
```

## 3. Install the Bot

```bash
# Clone the repository
git clone <repo-url> ~/TgInviteBot
cd ~/TgInviteBot

# Create a virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install .
```

## 4. Configuration

```bash
cp .env.example .env
nano .env
```

Required variables:

```env
BOT_TOKEN=123456:ABC-DEF...
ADMIN_CHAT_ID=-100123456789
```

### How to find ADMIN_CHAT_ID

If you don't know your admin group's ID:

1. Leave `ADMIN_CHAT_ID=` empty (or set to `0`) in `.env`
2. Start the bot: `python -m bot.main`
3. Send `/chatid` in the target group (the bot must be a member)
4. The bot will reply with the exact `.env` line to copy: `ADMIN_CHAT_ID=-100...`
5. Paste the value into `.env`
6. Restart the bot

Optional (have defaults):

```env
BOT_LANG=en
SQLITE_PATH=/home/tgbot/TgInviteBot/data/bot.db
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
DEFAULT_TIMEOUT_MINUTES=30
DEFAULT_MIN_RESPONSE_LENGTH=50
DEFAULT_AI_VALIDATION=true
DEFAULT_BAN_ON_REMOVE=false
```

## 5. Verify Startup

```bash
source .venv/bin/activate
python -m bot.main
# Ctrl+C after verifying the bot starts without errors
```

## 6. Systemd Service

Create `/etc/systemd/system/tgbot.service`:

```ini
[Unit]
Description=Telegram Onboarding Bot
After=network.target

[Service]
Type=simple
User=tgbot
Group=tgbot
WorkingDirectory=/home/tgbot/TgInviteBot
ExecStart=/home/tgbot/TgInviteBot/.venv/bin/python -m bot.main
Restart=always
RestartSec=5
EnvironmentFile=/home/tgbot/TgInviteBot/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbot
sudo systemctl start tgbot
sudo systemctl status tgbot    # check status
sudo journalctl -u tgbot -f   # view logs
```

## 7. Automatic Backups (cron)

As the `tgbot` user:

```bash
crontab -e
```

Add the line:

```cron
# Backup the DB daily at 3:00 AM
0 3 * * * SQLITE_PATH=/home/tgbot/TgInviteBot/data/bot.db BACKUP_DIR=/home/tgbot/backups /home/tgbot/TgInviteBot/scripts/backup.sh >> /home/tgbot/backups/cron.log 2>&1
```

## 8. Updating the Bot

```bash
sudo su - tgbot
cd ~/TgInviteBot
git pull
source .venv/bin/activate
pip install .
exit
sudo systemctl restart tgbot
```

## 9. Post-Deploy Checklist

- [ ] `systemctl status tgbot` — active (running)
- [ ] Send a message to the bot in Telegram — it responds
- [ ] Add the bot to a test group (as admin!)
- [ ] Verify a new member gets a welcome message
- [ ] Check `/pending` in the admin chat
- [ ] Verify `data/bot.db` was created
- [ ] Test backup: `./scripts/backup.sh`

## Notes

- Database migrations run automatically on bot startup
- Backups keep the last 30 copies; older ones are deleted automatically
- If the bot crashes, systemd restarts it after 5 seconds
