# Telegram Onboarding Bot

Бот для автоматического онбординга новых участников в Telegram-группах. Требует от новых участников представиться текстом, проверяет ответ через AI (OpenAI) и удаляет тех, кто не ответил в отведённое время.

## Возможности

- **Автоматическое приветствие** новых участников с настраиваемым шаблоном
- **AI-валидация** ответов через OpenAI (gpt-4o-mini)
- **Таймер удаления** — автоматическое удаление тех, кто не представился
- **Мульти-чат** — один бот обслуживает неограниченное количество групп
- **Per-chat настройки** — таймаут, длина ответа, AI-валидация и др.
- **Админский чат** — уведомления + inline-кнопки (одобрить/удалить/забанить)
- **Whitelist** — повторный вход без онбординга
- **Восстановление таймеров** после перезапуска бота

## Стек

- Python 3.11+, aiogram 3.x, asyncpg, APScheduler, OpenAI API
- PostgreSQL (Supabase)

## Быстрый старт

### 1. Настройка

```bash
cp .env.example .env
# Заполните .env: BOT_TOKEN, ADMIN_CHAT_ID, DATABASE_URL, OPENAI_API_KEY
```

### 2. Миграции

```bash
python -m migrations.run_migrations
```

### 3. Запуск

```bash
pip install -r requirements.txt
python -m bot.main
```

### Docker

```bash
docker-compose up -d
```

## Переменные окружения

| Переменная | Описание | Обязательная |
|-----------|----------|:----------:|
| `BOT_TOKEN` | Токен Telegram бота | да |
| `ADMIN_CHAT_ID` | ID чата для уведомлений администраторам | да |
| `DATABASE_URL` | PostgreSQL connection string | да |
| `OPENAI_API_KEY` | Ключ OpenAI API | нет* |
| `OPENAI_MODEL` | Модель OpenAI (default: gpt-4o-mini) | нет |
| `DEFAULT_TIMEOUT_MINUTES` | Таймаут ответа по умолчанию (default: 15) | нет |
| `DEFAULT_MIN_RESPONSE_LENGTH` | Мин. длина ответа (default: 10) | нет |

\* Без ключа AI-валидация будет отключена, все ответы автоматически одобряются.

## Админ-команды

Все команды работают только в админском чате (`ADMIN_CHAT_ID`).

| Команда | Описание |
|---------|----------|
| `/pending [chat_id]` | Список ожидающих участников |
| `/approve <chat_id> <user_id>` | Одобрить участника |
| `/remove <chat_id> <user_id>` | Удалить участника |
| `/ban <chat_id> <user_id>` | Забанить участника |
| `/whitelist <chat_id> <user_id>` | Добавить в whitelist |
| `/status <chat_id> <user_id>` | Показать статус участника |
| `/config <chat_id> [key=value ...]` | Настройки чата |

### Настраиваемые параметры (/config)

- `timeout_minutes` — таймаут ответа (минуты)
- `min_response_length` — минимальная длина ответа
- `ai_validation_enabled` — AI-валидация (true/false)
- `ban_on_remove` — банить при удалении (true/false)
- `ban_duration_hours` — длительность бана (число или null)
- `whitelist_enabled` — whitelist (true/false)
- `ignore_bots` — игнорировать ботов (true/false)
- `is_active` — активность бота в чате (true/false)
- `welcome_text` — текст приветствия (поддерживает {timeout})

## Бэкапы

```bash
# Бэкап
./scripts/backup.sh

# Восстановление
./scripts/restore.sh backups/backup_20260101_120000.sql.gz [target_db_url]
```

## Тесты

```bash
pip install pytest pytest-asyncio
pytest tests/
```

## Структура проекта

```
bot/
├── main.py              # Точка входа
├── config.py            # Конфигурация (.env)
├── db/                  # Слой работы с БД
│   ├── connection.py    # Пул соединений asyncpg
│   ├── members.py       # CRUD group_members
│   ├── settings.py      # CRUD chat_settings
│   └── events.py        # Логирование событий
├── handlers/            # Обработчики Telegram-событий
│   ├── new_member.py    # Вход нового участника
│   ├── message.py       # Ответы на онбординг
│   ├── member_left.py   # Выход участника
│   └── admin.py         # Админ-команды + inline-кнопки
├── services/            # Бизнес-логика
│   ├── onboarding.py    # Основной сценарий
│   ├── scheduler.py     # Таймеры (APScheduler)
│   ├── ai_validator.py  # Валидация через OpenAI
│   └── notifier.py      # Уведомления в админский чат
├── middlewares/
│   └── rate_limit.py    # Rate limiting
└── utils/
    └── template.py      # Подстановка переменных в шаблоны
```
