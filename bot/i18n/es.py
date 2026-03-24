"""Spanish translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "{user}, mensaje demasiado corto. Mínimo {min_len} caracteres.",
    "Thanks for the introduction! Welcome to the group.":
        "¡Gracias por la presentación! Bienvenido al grupo.",
    "{user}, please introduce yourself with text.":
        "{user}, por favor, preséntate con texto.",

    # --- Notifier (admin chat) ---
    "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction":
        "Nuevo miembro en <b>{chat}</b>\nUsuario: {user}\nEstado: esperando presentación",
    "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}":
        "#Presentación {user} en <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
    "#Error {user} in <b>{chat}</b>\n{error}":
        "#Error {user} en <b>{chat}</b>\n{error}",
    "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.":
        "#Timeout {user} en <b>{chat}</b>\nNo se presentó y fue eliminado.",
    "Approve": "Aprobar",
    "Remove": "Eliminar",
    "Ban": "Bloquear",

    # --- Admin callbacks ---
    "User approved": "Usuario aprobado",
    "User not found": "Usuario no encontrado",
    "--- APPROVED ---": "--- APROBADO ---",
    "User removed": "Usuario eliminado",
    "Could not remove": "No se pudo eliminar",
    "--- REMOVED ---": "--- ELIMINADO ---",
    "User banned": "Usuario bloqueado",
    "Could not ban": "No se pudo bloquear",
    "--- BANNED ---": "--- BLOQUEADO ---",

    # --- Admin commands ---
    "No pending members.": "No hay miembros pendientes.",
    "Pending: {count}": "Pendientes: {count}",
    "User not found.": "Usuario no encontrado.",
    "Unknown key: {name}": "Clave desconocida: {name}",
    "Invalid integer for {name}: {value}": "Número inválido para {name}: {value}",
    "Settings for chat {chat_id} updated.": "Configuración del chat {chat_id} actualizada.",
    "Chat not found.": "Chat no encontrado.",

    "Settings for chat {chat_id}:": "Configuración del chat {chat_id}:",

    # --- AI validator ---
    "ai_system_prompt": (
        "Eres un moderador de grupo. Un nuevo usuario se unió y debe presentarse.\n"
        "Acepta el texto si contiene al menos dos de: nombre, profesión/formación, motivo de ingreso.\n"
        "Rechaza spam, caracteres aleatorios, una sola palabra o mensajes fuera de tema.\n\n"
        "Ejemplos:\n"
        '- "Hola, soy María, desarrolladora, interesada en AI" → {"valid": true, "reason": "nombre y profesión"}\n'
        '- "hola" → {"valid": false, "reason": "demasiado vago, sin detalles"}\n\n'
        "Responde SOLO con JSON puro (sin markdown, sin bloques de código):\n"
        '{"valid": true, "reason": "..."} o {"valid": false, "reason": "..."}'
    ),
    "Introduction text:\n\n{text}": "Texto de presentación:\n\n{text}",
}
