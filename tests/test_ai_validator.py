import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.ai_validator import validate_response


@pytest.fixture(autouse=True)
def _reset_client():
    """Reset the global OpenAI client between tests."""
    import bot.services.ai_validator as mod
    mod._client = None
    yield
    mod._client = None


@pytest.mark.asyncio
async def test_validate_no_api_key():
    """Without API key, should auto-approve."""
    with patch("bot.services.ai_validator.config") as mock_config:
        mock_config.openai_api_key = ""
        result = await validate_response("Привет, меня зовут Иван")
        assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_valid_response():
    """AI returns valid=true."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {"valid": True, "reason": "Good introduction"}
    )

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("bot.services.ai_validator.config") as mock_config:
        mock_config.openai_api_key = "test-key"
        mock_config.openai_model = "gpt-4.1-mini"
        with patch("bot.services.ai_validator._get_client", return_value=mock_client):
            result = await validate_response("Привет! Меня зовут Иван, я разработчик.")
            assert result["valid"] is True


@pytest.mark.asyncio
async def test_validate_invalid_response():
    """AI returns valid=false."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps(
        {"valid": False, "reason": "Spam message"}
    )

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("bot.services.ai_validator.config") as mock_config:
        mock_config.openai_api_key = "test-key"
        mock_config.openai_model = "gpt-4.1-mini"
        with patch("bot.services.ai_validator._get_client", return_value=mock_client):
            result = await validate_response("Buy cheap stuff!")
            assert result["valid"] is False
