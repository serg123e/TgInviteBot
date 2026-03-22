# План реализации Telegram Onboarding Bot

## Доработки к исходному ТЗ

### Уточнения
- **OpenAI API** — используется для валидации ответов (осмысленность, не спам, не мусор)
- **Приветствие** — отправляется только в группу, остаётся в чате
- **Управление** — только через Telegram-команды в админском чате, без веб-панели
- **Мульти-чат** — один бот обслуживает много групп, у каждой свои настройки
- **Админский чат** — один общий для всех групп, туда приходят уведомления о новых участниках

### Добавленные компоненты (отсутствовали в ТЗ)

1. **Таблица `chat_settings`** — per-chat конфигурация (приветствие, таймаут, мин. длина и т.д.)
2. **AI-валидация ответов** — OpenAI оценивает, является ли ответ осмысленным представлением
3. **Rate limiting** — очередь отправки сообщений для защиты от Telegram flood control
4. **Проверка прав бота** — при добавлении в группу проверять, что бот — администратор
5. **Скрипты бэкапа/восстановления** — pg_dump + скрипт для восстановления на другой БД
6. **Миграции** — через SQL-файлы с версионированием

---

## Стек технологий

| Компонент | Технология | Обоснование |
|-----------|-----------|-------------|
| Язык | Python 3.11+ | По требованию |
| Бот-фреймворк | aiogram 3.x | Асинхронный, зрелый, middleware, роутеры |
| БД | Supabase (PostgreSQL) | По требованию |
| DB-клиент | asyncpg + supabase-py | asyncpg для основных операций, supabase-py для REST API |
| Таймеры | APScheduler | Персистентные джобы, легче Celery |
| AI | OpenAI API (gpt-4o-mini) | Дешёвый и быстрый для валидации текста |
| Конфиг | python-dotenv + БД | Глобальное в .env, per-chat в таблице |
| Бэкапы | pg_dump + cron | Просто и надёжно |

---

## Модель данных (доработанная)

### Таблица `chat_settings`
```sql
CREATE TABLE chat_settings (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT UNIQUE NOT NULL,
    chat_title TEXT,
    welcome_text TEXT NOT NULL DEFAULT 'Здравствуйте! Представьтесь в течение {timeout} минут.',
    timeout_minutes INT NOT NULL DEFAULT 15,
    min_response_length INT NOT NULL DEFAULT 10,
    ai_validation_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ban_on_remove BOOLEAN NOT NULL DEFAULT FALSE,
    ban_duration_hours INT DEFAULT NULL,  -- NULL = перманентный бан, если ban_on_remove=true
    whitelist_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ignore_bots BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Таблица `group_members`
```sql
CREATE TABLE group_members (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    telegram_user_id BIGINT NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    prompt_sent_at TIMESTAMPTZ,
    prompt_message_id BIGINT,  -- для возможного удаления приветствия
    response_text TEXT,
    responded_at TIMESTAMPTZ,
    ai_validation_result JSONB,  -- результат проверки OpenAI
    status TEXT NOT NULL DEFAULT 'joined',
    removed_at TIMESTAMPTZ,
    removal_reason TEXT,
    is_whitelisted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(chat_id, telegram_user_id)
);
```

### Таблица `event_logs`
```sql
CREATE TABLE event_logs (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT,
    telegram_user_id BIGINT,
    event_type TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Статусы (enum-like)
- `joined` — вошёл в группу
- `prompt_sent` — приветствие отправлено
- `responded` — ответил (ожидает AI-валидацию)
- `approved` — одобрен (автоматически или модератором)
- `rejected` — ответ не прошёл AI-валидацию, ожидает решения модератора
- `removed_no_response` — удалён за молчание
- `removed_rejected` — удалён после отклонения ответа
- `removed_manual` — удалён модератором
- `left` — ушёл сам
- `error` — ошибка обработки

---

## Структура проекта

```
TgInviteBot/
├── bot/
│   ├── __init__.py
│   ├── main.py              # Точка входа, инициализация бота
│   ├── config.py             # Загрузка .env, глобальные настройки
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py     # Пул соединений asyncpg
│   │   ├── members.py        # CRUD для group_members
│   │   ├── settings.py       # CRUD для chat_settings
│   │   └── events.py         # Запись event_logs
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── new_member.py     # Обработка входа нового участника
│   │   ├── message.py        # Обработка сообщений (ответов на onboarding)
│   │   ├── member_left.py    # Обработка выхода участника
│   │   └── admin.py          # Админ-команды
│   ├── services/
│   │   ├── __init__.py
│   │   ├── onboarding.py     # Бизнес-логика onboarding
│   │   ├── scheduler.py      # APScheduler — таймеры удаления
│   │   ├── ai_validator.py   # Валидация через OpenAI
│   │   └── notifier.py       # Уведомления в админский чат
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── rate_limit.py     # Rate limiting для Telegram API
│   └── utils/
│       ├── __init__.py
│       └── template.py       # Подстановка переменных в шаблоны
├── migrations/
│   ├── 001_initial.sql
│   └── run_migrations.py
├── scripts/
│   ├── backup.sh             # pg_dump скрипт
│   └── restore.sh            # Восстановление на другую БД
├── tests/
│   ├── test_onboarding.py
│   ├── test_ai_validator.py
│   └── test_template.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Этапы реализации

### Этап 1: Фундамент (каркас)
1. Инициализация проекта: requirements.txt, .env.example, config.py
2. Подключение к Supabase (asyncpg)
3. SQL-миграции — создание таблиц
4. Базовый бот на aiogram 3 — запуск, регистрация роутеров

### Этап 2: Основной сценарий onboarding
5. Обработчик входа нового участника (new_member handler)
6. Отправка приветственного сообщения с шаблоном
7. APScheduler — таймер на удаление через N минут
8. Обработчик сообщений — распознавание ответа на onboarding
9. Удаление участника при отсутствии ответа
10. Сохранение ответа в БД, смена статуса

### Этап 3: AI-валидация
11. Интеграция OpenAI API — проверка осмысленности ответа
12. Логика: ответ прошёл → approved, не прошёл → rejected + уведомление модераторам

### Этап 4: Мульти-чат + админский чат
13. Таблица chat_settings — per-chat конфигурация
14. Уведомления в админский чат (новый участник представился + кнопки)
15. Обработка inline-кнопок (одобрить/удалить/забанить)

### Этап 5: Админ-команды
16. /pending — список ожидающих
17. /approve @username — одобрить
18. /remove @username — удалить
19. /whitelist @username — добавить в whitelist
20. /status @username — статус пользователя
21. /config — показать/изменить настройки чата

### Этап 6: Whitelist + edge cases
22. Whitelist логика — пропуск повторного входа
23. Обработка выхода участника (закрытие сценария)
24. Обработка дублирования событий от Telegram
25. Проверка прав бота при добавлении в группу
26. Восстановление таймеров после перезапуска

### Этап 7: Инфраструктура
27. Скрипты бэкапа/восстановления БД
28. Dockerfile + docker-compose
29. Логирование (structured logging)
30. Базовые тесты

### Этап 8: Документация
31. README с инструкциями запуска и деплоя
32. Описание переменных окружения
33. Описание админ-команд
34. Ограничения решения

---

## Ключевые решения

### Как распознать ответ на onboarding?
Бот считает ответом **любое текстовое сообщение** от пользователя со статусом `joined` или `prompt_sent` в данном чате. Не reply на конкретное сообщение, а просто первое текстовое сообщение. Стикеры, фото, голосовые — игнорируются (с уведомлением "пожалуйста, напишите текстом").

### Как работает AI-валидация?
Промпт для GPT-4o-mini:
```
Пользователь вступил в группу и должен представиться.
Оцени, является ли следующий текст осмысленным представлением (имя, чем занимается, зачем пришёл).
Ответь JSON: {"valid": true/false, "reason": "краткое пояснение"}
Текст: "{response_text}"
```
Если valid=true → статус `approved`. Если false → статус `rejected`, уведомление модераторам.

### Как работают таймеры после перезапуска?
При старте бот запрашивает из БД всех участников со статусами `joined`/`prompt_sent`, считает оставшееся время (timeout - (now - joined_at)), и ставит таймеры через APScheduler. Если время уже истекло — сразу запускает удаление.

### Rate limiting
Очередь отправки сообщений с интервалом 50мс между сообщениями (Telegram лимит ~30 msg/sec для бота). При 429 ошибке — exponential backoff.

---

## Переменные окружения

```env
# Telegram
BOT_TOKEN=
ADMIN_CHAT_ID=

# Supabase / PostgreSQL
DATABASE_URL=postgresql://user:pass@host:port/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=

# OpenAI
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Defaults (можно переопределить per-chat через команды)
DEFAULT_TIMEOUT_MINUTES=15
DEFAULT_MIN_RESPONSE_LENGTH=10
DEFAULT_AI_VALIDATION=true
DEFAULT_WHITELIST_ENABLED=true
DEFAULT_BAN_ON_REMOVE=false

# Backup
BACKUP_DIR=/backups
```
