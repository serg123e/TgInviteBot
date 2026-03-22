from __future__ import annotations

import logging

from openai import AsyncOpenAI
from pydantic import BaseModel

from bot.config import config
from bot.i18n import has, t

log = logging.getLogger(__name__)


class AIResult(BaseModel):
    valid: bool
    reason: str = ""


_client: AsyncOpenAI | None = None

SYSTEM_PROMPT_EN = (
    "You are a group moderator. A new user has joined and must introduce themselves.\n"
    "Evaluate whether the following text is a meaningful introduction "
    "(name, occupation, reason for joining).\n"
    'Respond with ONLY valid JSON without markdown: '
    '{"valid": true/false, "reason": "brief explanation"}'
)


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
        return AIResult(valid=True, reason="AI validation disabled (no API key)").model_dump()

    try:
        client = _get_client()
        system_prompt = t("ai_system_prompt") if has("ai_system_prompt") else SYSTEM_PROMPT_EN
        resp = await client.chat.completions.create(
            model=config.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": t("Introduction text:\n\n{text}", text=text[:1000])},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        content = (resp.choices[0].message.content or "").strip()
        result = AIResult.model_validate_json(content)
        return result.model_dump()
    except Exception as e:
        log.error("AI validation error: %s", e)
        return AIResult(valid=False, reason=f"AI error, pending manual review: {e}").model_dump()
