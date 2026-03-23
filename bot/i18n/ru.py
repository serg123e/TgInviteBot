"""Russian translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "{user}, сообщение слишком короткое. Минимум {min_len} символов.",
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
    "User not found.": "Пользователь не найден.",
    "Unknown key: {name}": "Неизвестный ключ: {name}",
    "Invalid integer for {name}: {value}": "Некорректное число для {name}: {value}",
    "Settings for chat {chat_id} updated.": "Настройки чата {chat_id} обновлены.",
    "Chat not found.": "Чат не найден.",

    "Settings for chat {chat_id}:": "Настройки чата {chat_id}:",

    # --- AI validator ---
    "ai_system_prompt": (
        "Ты — модератор группы. Новый пользователь вступил и должен представиться.\n"
        "Прими текст, если он содержит хотя бы два из: имя, род занятий, зачем пришёл.\n"
        "Отклони спам, случайные символы, одно слово или сообщения не по теме.\n\n"
        "Примеры:\n"
        '- "Привет, я Алексей, разработчик, интересуюсь AI" → {"valid": true, "reason": "имя и род занятий"}\n'
        '- "привет" → {"valid": false, "reason": "слишком расплывчато, нет деталей"}\n\n'
        "Ответь ТОЛЬКО сырым JSON (без markdown, без блоков кода):\n"
        '{"valid": true, "reason": "..."} или {"valid": false, "reason": "..."}'
    ),
    "Introduction text:\n\n{text}": "Текст представления:\n\n{text}",
}
