"""Russian translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "@{user}, сообщение слишком короткое. Минимум {min_len} символов.",
    "Thanks for the introduction! Welcome to the group.":
        "Спасибо за представление! Добро пожаловать в группу.",
    "{user}, please introduce yourself with text.":
        "{user}, пожалуйста, представьтесь текстом.",

    # --- Notifier (admin chat) ---
    "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction":
        "Новый участник в <b>{chat}</b>\nПользователь: {user}\nСтатус: ожидает представления",
    "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}":
        "#Представление {user} в <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
    "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.":
        "#Таймаут {user} в <b>{chat}</b>\nНе представился и был удалён.",
    "Approve": "Одобрить",
    "Remove": "Удалить",
    "Ban": "Забанить",

    # --- Admin callbacks ---
    "User approved": "Пользователь одобрен",
    "User not found": "Пользователь не найден",
    "--- APPROVED ---": "--- ОДОБРЕН ---",
    "User removed": "Пользователь удалён",
    "Could not remove": "Не удалось удалить",
    "--- REMOVED ---": "--- УДАЛЁН ---",
    "User banned": "Пользователь забанен",
    "Could not ban": "Не удалось забанить",
    "--- BANNED ---": "--- ЗАБАНЕН ---",

    # --- Admin commands ---
    "No pending members.": "Нет ожидающих участников.",
    "Pending: {count}": "Ожидающих: {count}",
    "Approved.": "Одобрен.",
    "Not found.": "Не найден.",
    "Removed.": "Удалён.",
    "Could not remove.": "Не удалось удалить.",
    "Banned.": "Забанен.",
    "Could not ban.": "Не удалось забанить.",
    "User {user_id} added to whitelist and approved.":
        "Пользователь {user_id} добавлен в whitelist и одобрен.",
    "User not found.": "Пользователь не найден.",
    "Unknown key: {name}": "Неизвестный ключ: {name}",
    "Invalid integer for {name}: {value}": "Некорректное число для {name}: {value}",
    "Settings for chat {chat_id} updated.": "Настройки чата {chat_id} обновлены.",
    "Chat not found.": "Чат не найден.",
    "yes": "да",
    "no": "нет",

    # --- Status display ---
    "User: {user}\nChat: {chat_id}\nStatus: {status}\nJoined: {joined}\nWhitelisted: {wl}":
        "Пользователь: {user}\nЧат: {chat_id}\nСтатус: {status}\nВступил: {joined}\nWhitelisted: {wl}",
    "Response: {text}": "Ответ: {text}",
    "AI: {result}": "AI: {result}",
    "Settings for chat {chat_id}:": "Настройки чата {chat_id}:",

    # --- AI validator ---
    "ai_system_prompt": (
        "Ты — модератор группы. Пользователь вступил в группу и должен представиться.\n"
        "Оцени, является ли следующий текст осмысленным представлением "
        "(имя, чем занимается, зачем пришёл).\n"
        "Ответь ТОЛЬКО валидным JSON без markdown: "
        '{\"valid\": true/false, \"reason\": \"краткое пояснение\"}'
    ),
    "Introduction text:\n\n{text}": "Текст представления:\n\n{text}",
}
