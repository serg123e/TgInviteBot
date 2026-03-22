# Деплой без Docker (Linux + systemd)

## 1. Требования к серверу

- Ubuntu 22.04+ / Debian 12+ (или любой Linux с systemd)
- Python 3.11+
- sqlite3 (обычно уже установлен)
- Доступ в интернет (Telegram API, OpenAI API)

## 2. Подготовка сервера

```bash
# Обновить пакеты
sudo apt update && sudo apt upgrade -y

# Установить Python и инструменты
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Создать пользователя для бота
sudo useradd -m -s /bin/bash tgbot
sudo su - tgbot
```

## 3. Установка бота

```bash
# Склонировать репозиторий
git clone <repo-url> ~/TgInviteBot
cd ~/TgInviteBot

# Создать виртуальное окружение
python3.11 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

## 4. Конфигурация

```bash
cp .env.example .env
nano .env
```

Обязательные переменные:

```env
BOT_TOKEN=123456:ABC-DEF...
ADMIN_CHAT_ID=-100123456789
```

Опциональные (есть значения по умолчанию):

```env
SQLITE_PATH=/home/tgbot/TgInviteBot/data/bot.db
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
DEFAULT_TIMEOUT_MINUTES=15
DEFAULT_MIN_RESPONSE_LENGTH=10
DEFAULT_AI_VALIDATION=true
DEFAULT_WHITELIST_ENABLED=true
DEFAULT_BAN_ON_REMOVE=false
```

## 5. Проверка запуска

```bash
source .venv/bin/activate
python -m bot.main
# Ctrl+C после проверки что бот стартует без ошибок
```

## 6. Systemd-сервис

Создать файл `/etc/systemd/system/tgbot.service`:

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

Активировать:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbot
sudo systemctl start tgbot
sudo systemctl status tgbot    # проверить статус
sudo journalctl -u tgbot -f   # смотреть логи
```

## 7. Автобэкап (cron)

От пользователя `tgbot`:

```bash
crontab -e
```

Добавить строку:

```cron
# Бэкап БД каждый день в 3:00
0 3 * * * SQLITE_PATH=/home/tgbot/TgInviteBot/data/bot.db BACKUP_DIR=/home/tgbot/backups /home/tgbot/TgInviteBot/scripts/backup.sh >> /home/tgbot/backups/cron.log 2>&1
```

## 8. Обновление бота

```bash
sudo su - tgbot
cd ~/TgInviteBot
git pull
source .venv/bin/activate
pip install -r requirements.txt
exit
sudo systemctl restart tgbot
```

## 9. Чеклист после деплоя

- [ ] `systemctl status tgbot` — active (running)
- [ ] Написать боту в Telegram — отвечает
- [ ] Добавить бота в тестовую группу (админом!)
- [ ] Проверить вход нового участника — приветствие появляется
- [ ] Проверить `/pending` в админском чате
- [ ] Проверить что файл `data/bot.db` создался
- [ ] Проверить что бэкап работает: `./scripts/backup.sh`

## Примечания

- Миграции БД запускаются автоматически при старте бота
- Бэкап хранит последние 30 копий, старые удаляются автоматически
- При падении бота systemd перезапустит его через 5 секунд
