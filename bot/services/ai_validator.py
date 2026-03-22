from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from bot.config import config

log = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None

SYSTEM_PROMPT = """Ты — модератор группы. Пользователь вступил в группу и должен представиться.
Оцени, является ли следующий текст осмысленным представлением (имя, чем занимается, зачем пришёл).
Ответь ТОЛЬКО валидным JSON без markdown: {"valid": true/false, "reason": "краткое пояснение на русском"}"""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=config.openai_api_key)
    return _client


async def validate_response(text: str) -> dict:
    """Validate an introduction text using OpenAI.

    Returns dict with keys: valid (bool), reason (str).
    """
    if not config.openai_api_key:
        log.warning("OpenAI API key not set, auto-approving")
        return {"valid": True, "reason": "AI validation disabled (no API key)"}

    try:
        client = _get_client()
        resp = await client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Текст представления:\n\n{text}"},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        content = resp.choices[0].message.content.strip()
        result = json.loads(content)
        if "valid" not in result:
            raise ValueError("Missing 'valid' key")
        return result
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        log.error("Failed to parse AI response: %s", e)
        return {"valid": True, "reason": f"AI parse error, auto-approved: {e}"}
    except Exception as e:
        log.error("OpenAI API error: %s", e)
        return {"valid": True, "reason": f"AI API error, auto-approved: {e}"}
