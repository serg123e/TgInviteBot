"""Indonesian translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "{user}, pesan terlalu pendek. Minimal {min_len} karakter.",
    "Thanks for the introduction! Welcome to the group.":
        "Terima kasih atas perkenalannya! Selamat datang di grup.",
    "{user}, please introduce yourself with text.":
        "{user}, silakan perkenalkan diri Anda dengan teks.",

    # --- Notifier (admin chat) ---
    "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction":
        "Anggota baru di <b>{chat}</b>\nPengguna: {user}\nStatus: menunggu perkenalan",
    "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}":
        "#Perkenalan {user} di <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
    "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.":
        "#Timeout {user} di <b>{chat}</b>\nTidak memperkenalkan diri dan telah dihapus.",
    "Approve": "Setujui",
    "Remove": "Hapus",
    "Ban": "Blokir",

    # --- Admin callbacks ---
    "User approved": "Pengguna disetujui",
    "User not found": "Pengguna tidak ditemukan",
    "--- APPROVED ---": "--- DISETUJUI ---",
    "User removed": "Pengguna dihapus",
    "Could not remove": "Tidak dapat menghapus",
    "--- REMOVED ---": "--- DIHAPUS ---",
    "User banned": "Pengguna diblokir",
    "Could not ban": "Tidak dapat memblokir",
    "--- BANNED ---": "--- DIBLOKIR ---",

    # --- Admin commands ---
    "No pending members.": "Tidak ada anggota yang menunggu.",
    "Pending: {count}": "Menunggu: {count}",
    "Approved.": "Disetujui.",
    "Not found.": "Tidak ditemukan.",
    "Removed.": "Dihapus.",
    "Could not remove.": "Tidak dapat menghapus.",
    "Banned.": "Diblokir.",
    "Could not ban.": "Tidak dapat memblokir.",
    "User {user_id} added to whitelist and approved.":
        "Pengguna {user_id} ditambahkan ke whitelist dan disetujui.",
    "User not found.": "Pengguna tidak ditemukan.",
    "Unknown key: {name}": "Kunci tidak dikenal: {name}",
    "Invalid integer for {name}: {value}": "Angka tidak valid untuk {name}: {value}",
    "Settings for chat {chat_id} updated.": "Pengaturan chat {chat_id} diperbarui.",
    "Chat not found.": "Chat tidak ditemukan.",
    "yes": "ya",
    "no": "tidak",

    # --- Status display ---
    "User: {user}\nChat: {chat_id}\nStatus: {status}\nJoined: {joined}\nWhitelisted: {wl}":
        "Pengguna: {user}\nChat: {chat_id}\nStatus: {status}\nBergabung: {joined}\nWhitelisted: {wl}",
    "Response: {text}": "Respons: {text}",
    "AI: {result}": "AI: {result}",
    "Settings for chat {chat_id}:": "Pengaturan chat {chat_id}:",

    # --- AI validator ---
    "ai_system_prompt": (
        "Anda adalah moderator grup. Pengguna baru telah bergabung dan harus memperkenalkan diri.\n"
        "Terima teks jika mengandung setidaknya dua dari: nama, pekerjaan/latar belakang, alasan bergabung.\n"
        "Tolak spam, karakter acak, satu kata saja, atau pesan di luar topik.\n\n"
        "Contoh:\n"
        '- "Halo, saya Budi, developer, tertarik dengan AI" → {"valid": true, "reason": "nama dan pekerjaan"}\n'
        '- "hai" → {"valid": false, "reason": "terlalu samar, tidak ada detail"}\n\n'
        "Jawab HANYA dengan JSON murni (tanpa markdown, tanpa blok kode):\n"
        '{"valid": true, "reason": "..."} atau {"valid": false, "reason": "..."}'
    ),
    "Introduction text:\n\n{text}": "Teks perkenalan:\n\n{text}",
}
