"""Portuguese translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "{user}, mensagem muito curta. Mínimo de {min_len} caracteres.",
    "Thanks for the introduction! Welcome to the group.":
        "Obrigado pela apresentação! Bem-vindo ao grupo.",
    "{user}, please introduce yourself with text.":
        "{user}, por favor, apresente-se com texto.",

    # --- Notifier (admin chat) ---
    "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction":
        "Novo membro em <b>{chat}</b>\nUsuário: {user}\nStatus: aguardando apresentação",
    "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}":
        "#Apresentação {user} em <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
    "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.":
        "#Timeout {user} em <b>{chat}</b>\nNão se apresentou e foi removido.",
    "Approve": "Aprovar",
    "Remove": "Remover",
    "Ban": "Banir",

    # --- Admin callbacks ---
    "User approved": "Usuário aprovado",
    "User not found": "Usuário não encontrado",
    "--- APPROVED ---": "--- APROVADO ---",
    "User removed": "Usuário removido",
    "Could not remove": "Não foi possível remover",
    "--- REMOVED ---": "--- REMOVIDO ---",
    "User banned": "Usuário banido",
    "Could not ban": "Não foi possível banir",
    "--- BANNED ---": "--- BANIDO ---",

    # --- Admin commands ---
    "No pending members.": "Nenhum membro pendente.",
    "Pending: {count}": "Pendentes: {count}",
    "Unknown key: {name}": "Chave desconhecida: {name}",
    "Invalid integer for {name}: {value}": "Número inválido para {name}: {value}",
    "Settings for chat {chat_id} updated.": "Configurações do chat {chat_id} atualizadas.",
    "Chat not found.": "Chat não encontrado.",

    "Settings for chat {chat_id}:": "Configurações do chat {chat_id}:",

    # --- AI validator ---
    "ai_system_prompt": (
        "Você é um moderador de grupo. Um novo usuário entrou e deve se apresentar.\n"
        "Aceite o texto se contiver pelo menos dois de: nome, profissão/formação, motivo de entrada.\n"
        "Rejeite spam, caracteres aleatórios, uma única palavra ou mensagens fora do tema.\n\n"
        "Exemplos:\n"
        '- "Olá, sou o Pedro, desenvolvedor, interessado em AI" → {"valid": true, "reason": "nome e profissão"}\n'
        '- "oi" → {"valid": false, "reason": "muito vago, sem detalhes"}\n\n'
        "Responda APENAS com JSON puro (sem markdown, sem blocos de código):\n"
        '{"valid": true, "reason": "..."} ou {"valid": false, "reason": "..."}'
    ),
    "Introduction text:\n\n{text}": "Texto de apresentação:\n\n{text}",
}
