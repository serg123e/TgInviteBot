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
    "You are a group moderator. A new user joined and must introduce themselves.\n"
    "Evaluate whether the text is a meaningful introduction. Accept if it contains "
    "at least two of: name, occupation/background, reason for joining.\n"
    "Reject spam, random characters, single words, or off-topic messages.\n\n"
    "Examples:\n"
    '- "Hi, I\'m Alex, a developer interested in AI" → {"valid": true, "reason": "name and background"}\n'
    '- "hello" → {"valid": false, "reason": "too vague, no details"}\n\n'
    "Respond with ONLY raw JSON (no markdown, no code blocks):\n"
    '{"valid": true, "reason": "..."} or {"valid": false, "reason": "..."}'
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
        # Strip markdown code fences if model wraps JSON despite instructions
        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()
        result = AIResult.model_validate_json(content)
        return result.model_dump()
    except Exception as e:
        log.error("AI validation error: %s", e)
        return AIResult(valid=False, reason=f"AI error, pending manual review: {e}").model_dump()
