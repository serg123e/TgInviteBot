"""Vietnamese translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "{user}, tin nhắn quá ngắn. Tối thiểu {min_len} ký tự.",
    "Thanks for the introduction! Welcome to the group.":
        "Cảm ơn bạn đã giới thiệu! Chào mừng bạn đến nhóm.",
    "{user}, please introduce yourself with text.":
        "{user}, vui lòng giới thiệu bản thân bằng văn bản.",

    # --- Notifier (admin chat) ---
    "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction":
        "Thành viên mới trong <b>{chat}</b>\nNgười dùng: {user}\nTrạng thái: đang chờ giới thiệu",
    "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}":
        "#GiớiThiệu {user} trong <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
    "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.":
        "#HếtGiờ {user} trong <b>{chat}</b>\nKhông giới thiệu và đã bị xóa.",
    "Approve": "Chấp nhận",
    "Remove": "Xóa",
    "Ban": "Cấm",

    # --- Admin callbacks ---
    "User approved": "Đã chấp nhận người dùng",
    "User not found": "Không tìm thấy người dùng",
    "--- APPROVED ---": "--- ĐÃ CHẤP NHẬN ---",
    "User removed": "Đã xóa người dùng",
    "Could not remove": "Không thể xóa",
    "--- REMOVED ---": "--- ĐÃ XÓA ---",
    "User banned": "Đã cấm người dùng",
    "Could not ban": "Không thể cấm",
    "--- BANNED ---": "--- ĐÃ CẤM ---",

    # --- Admin commands ---
    "No pending members.": "Không có thành viên đang chờ.",
    "Pending: {count}": "Đang chờ: {count}",
    "Unknown key: {name}": "Khóa không xác định: {name}",
    "Invalid integer for {name}: {value}": "Số không hợp lệ cho {name}: {value}",
    "Settings for chat {chat_id} updated.": "Cài đặt cho chat {chat_id} đã được cập nhật.",
    "Chat not found.": "Không tìm thấy chat.",

    "Settings for chat {chat_id}:": "Cài đặt cho chat {chat_id}:",

    # --- AI validator ---
    "ai_system_prompt": (
        "Bạn là quản trị viên nhóm. Một người dùng mới đã tham gia và phải giới thiệu bản thân.\n"
        "Chấp nhận nếu văn bản chứa ít nhất hai trong: tên, nghề nghiệp, lý do tham gia.\n"
        "Từ chối spam, ký tự ngẫu nhiên, một từ duy nhất hoặc tin nhắn lạc đề.\n\n"
        "Ví dụ:\n"
        '- "Xin chào, tôi là Minh, lập trình viên, quan tâm đến AI" → {"valid": true, "reason": "tên và nghề nghiệp"}\n'
        '- "chào" → {"valid": false, "reason": "quá mơ hồ, không có chi tiết"}\n\n'
        "Trả lời CHỈ bằng JSON thuần (không markdown, không khối mã):\n"
        '{"valid": true, "reason": "..."} hoặc {"valid": false, "reason": "..."}'
    ),
    "Introduction text:\n\n{text}": "Văn bản giới thiệu:\n\n{text}",
}
