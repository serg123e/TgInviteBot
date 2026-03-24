"""Hindi translations. Keys are English defaults."""

MESSAGES: dict[str, str] = {
    # --- Onboarding (group-facing) ---
    "{user}, message too short. Minimum {min_len} characters.":
        "{user}, संदेश बहुत छोटा है। न्यूनतम {min_len} अक्षर।",
    "Thanks for the introduction! Welcome to the group.":
        "परिचय के लिए धन्यवाद! समूह में आपका स्वागत है।",
    "{user}, please introduce yourself with text.":
        "{user}, कृपया टेक्स्ट में अपना परिचय दें।",

    # --- Notifier (admin chat) ---
    "New member in <b>{chat}</b>\nUser: {user}\nStatus: awaiting introduction":
        "<b>{chat}</b> में नया सदस्य\nउपयोगकर्ता: {user}\nस्थिति: परिचय की प्रतीक्षा",
    "#Introduction {user} in <b>{chat}</b>\n\n<i>{intro}</i>\n\nAI: {status} — {reason}":
        "#परिचय {user} <b>{chat}</b> में\n\n<i>{intro}</i>\n\nAI: {status} — {reason}",
    "#Error {user} in <b>{chat}</b>\n{error}":
        "#त्रुटि {user} <b>{chat}</b> में\n{error}",
    "#Timeout {user} in <b>{chat}</b>\nDid not introduce and was removed.":
        "#समय_समाप्त {user} <b>{chat}</b> में\nपरिचय नहीं दिया और हटा दिया गया।",
    "Approve": "स्वीकृत करें",
    "Remove": "हटाएं",
    "Ban": "प्रतिबंधित करें",

    # --- Admin callbacks ---
    "User approved": "उपयोगकर्ता स्वीकृत",
    "User not found": "उपयोगकर्ता नहीं मिला",
    "--- APPROVED ---": "--- स्वीकृत ---",
    "User removed": "उपयोगकर्ता हटाया गया",
    "Could not remove": "हटा नहीं सके",
    "--- REMOVED ---": "--- हटाया गया ---",
    "User banned": "उपयोगकर्ता प्रतिबंधित",
    "Could not ban": "प्रतिबंधित नहीं कर सके",
    "--- BANNED ---": "--- प्रतिबंधित ---",

    # --- Admin commands ---
    "No pending members.": "कोई लंबित सदस्य नहीं।",
    "Pending: {count}": "लंबित: {count}",
    "User not found.": "उपयोगकर्ता नहीं मिला।",
    "Unknown key: {name}": "अज्ञात कुंजी: {name}",
    "Invalid integer for {name}: {value}": "{name} के लिए अमान्य संख्या: {value}",
    "Settings for chat {chat_id} updated.": "चैट {chat_id} की सेटिंग्स अपडेट की गईं।",
    "Chat not found.": "चैट नहीं मिला।",

    "Settings for chat {chat_id}:": "चैट {chat_id} की सेटिंग्स:",

    # --- AI validator ---
    "ai_system_prompt": (
        "तुम एक समूह मॉडरेटर हो। एक नया उपयोगकर्ता शामिल हुआ है और उसे अपना परिचय देना होगा।\n"
        "टेक्स्ट स्वीकार करो अगर उसमें कम से कम दो हों: नाम, पेशा/पृष्ठभूमि, शामिल होने का कारण।\n"
        "स्पैम, यादृच्छिक अक्षर, एक शब्द या विषय से हटकर संदेश अस्वीकार करो।\n\n"
        "उदाहरण:\n"
        '- "नमस्ते, मैं राहुल हूँ, डेवलपर, AI में रुचि है" → {"valid": true, "reason": "नाम और पेशा"}\n'
        '- "हेलो" → {"valid": false, "reason": "बहुत अस्पष्ट, कोई विवरण नहीं"}\n\n'
        "केवल raw JSON में उत्तर दो (कोई markdown नहीं, कोई code block नहीं):\n"
        '{"valid": true, "reason": "..."} या {"valid": false, "reason": "..."}'
    ),
    "Introduction text:\n\n{text}": "परिचय टेक्स्ट:\n\n{text}",
}
