import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _bool(val: str | None, default: bool = False) -> bool:
    if val is None:
        return default
    return val.lower() in ("true", "1", "yes")


@dataclass(frozen=True)
class Config:
    # Telegram
    bot_token: str = field(default_factory=lambda: os.environ.get("BOT_TOKEN", ""))
    admin_chat_id: int = field(
        default_factory=lambda: int(os.environ.get("ADMIN_CHAT_ID", "0"))
    )

    # Database
    sqlite_path: str = field(
        default_factory=lambda: os.environ.get("SQLITE_PATH", "data/bot.db")
    )

    # OpenAI
    openai_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    openai_model: str = field(
        default_factory=lambda: os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    )

    # Defaults
    default_timeout_minutes: int = field(
        default_factory=lambda: int(os.environ.get("DEFAULT_TIMEOUT_MINUTES", "15"))
    )
    default_min_response_length: int = field(
        default_factory=lambda: int(os.environ.get("DEFAULT_MIN_RESPONSE_LENGTH", "10"))
    )
    default_ai_validation: bool = field(
        default_factory=lambda: _bool(os.environ.get("DEFAULT_AI_VALIDATION"), True)
    )
    default_whitelist_enabled: bool = field(
        default_factory=lambda: _bool(os.environ.get("DEFAULT_WHITELIST_ENABLED"), True)
    )
    default_ban_on_remove: bool = field(
        default_factory=lambda: _bool(os.environ.get("DEFAULT_BAN_ON_REMOVE"), False)
    )


config = Config()
