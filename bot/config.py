from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    # Language
    lang: str = Field(default="en", validation_alias="BOT_LANG")

    # Telegram
    bot_token: str = ""
    admin_chat_id: int = 0

    # Database
    sqlite_path: str = "data/bot.db"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"

    # Defaults
    default_timeout_minutes: int = 30
    default_min_response_length: int = 50
    default_ai_validation: bool = True
    default_ban_on_remove: bool = False


config = Config()
