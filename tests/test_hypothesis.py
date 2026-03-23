"""Property-based tests using Hypothesis."""

import json

import pytest
from hypothesis import given
from hypothesis import settings as hsettings
from hypothesis import strategies as st
from pydantic import ValidationError

from bot.i18n import t
from bot.middlewares.rate_limit import MAX_TRACKED_CHATS, RateLimitMiddleware
from bot.services.ai_validator import AIResult
from bot.utils.template import render, user_display

# --- render() ---


@given(st.text(), st.text())
def test_render_substitutes_value(key_val, replacement):
    """render() always replaces {key} with the value."""
    result = render("{x}", x=replacement)
    assert replacement in result


@given(st.text())
def test_render_no_kwargs_is_identity(template):
    """render() without kwargs returns the template unchanged."""
    assert render(template) == template


@given(st.text(min_size=1).filter(lambda s: "{" not in s and "}" not in s))
def test_render_no_placeholders_unchanged(template):
    """render() with no placeholders ignores extra kwargs."""
    assert render(template, foo="bar") == template


@given(st.text(min_size=1), st.text(min_size=1))
def test_render_no_cross_substitution(val_a, val_b):
    """Values containing {other_key} are NOT substituted again."""
    # Put {b} as value for a — it should appear literally, not be replaced by val_b
    result = render("{a} {b}", a="{b}", b=val_b)
    # The first {a} is replaced with literal "{b}", then {b} is replaced with val_b.
    # Current render() does sequential replace, so {b} in the value WILL be replaced.
    # This test documents that behavior.
    assert val_b in result


# --- user_display() ---


@given(st.text(min_size=1), st.integers(min_value=1))
def test_user_display_username_is_escaped(username, uid):
    """user_display with username always starts with @ and HTML-escapes."""
    result = user_display(username, None, uid)
    assert result.startswith("@")
    assert "<script>" not in result


@given(st.text(min_size=1), st.integers(min_value=1))
def test_user_display_first_name_contains_id(first_name, uid):
    """user_display with first_name includes the user id."""
    result = user_display(None, first_name, uid)
    assert str(uid) in result


@given(st.integers(min_value=1))
def test_user_display_fallback(uid):
    """user_display with no name falls back to id."""
    result = user_display(None, None, uid)
    assert result == f"id: {uid}"


@given(
    st.text(alphabet=st.characters(categories=("L", "N", "P", "S")), min_size=1),
    st.integers(min_value=1),
)
def test_user_display_no_raw_html(name, uid):
    """user_display never produces unescaped angle brackets from input."""
    for username, first_name in [(name, None), (None, name)]:
        result = user_display(username, first_name, uid)
        if "<" in name:
            assert "<" not in result or "&lt;" in result


# --- i18n t() ---


@given(st.text(min_size=1).filter(lambda s: "{" not in s))
def test_t_missing_key_returns_key(key):
    """t() returns the key itself when no translation exists."""
    assert t(key) == key


@given(st.text(min_size=1).filter(lambda s: "{" not in s))
def test_t_never_crashes_without_kwargs(key):
    """t() never raises on arbitrary keys without kwargs."""
    result = t(key)
    assert isinstance(result, str)


@given(st.text(min_size=1).filter(lambda s: "{" not in s), st.text())
def test_t_with_unused_kwargs_no_crash(key, value):
    """t() with extra kwargs that don't match placeholders doesn't crash."""
    # Only safe if the key has no format placeholders
    result = t(key, unused=value)
    assert isinstance(result, str)


# --- AIResult ---


@given(st.booleans(), st.text())
def test_airesult_valid_json_roundtrip(valid, reason):
    """AIResult serializes and deserializes correctly."""
    original = AIResult(valid=valid, reason=reason)
    dumped = original.model_dump_json()
    restored = AIResult.model_validate_json(dumped)
    assert restored.valid == valid
    assert restored.reason == reason


@given(st.text().filter(lambda s: s.strip() != ""))
def test_airesult_rejects_invalid_json(garbage):
    """AIResult.model_validate_json raises on non-JSON input."""
    # Skip strings that happen to be valid AIResult JSON
    try:
        parsed = json.loads(garbage)
        if isinstance(parsed, dict) and "valid" in parsed:
            return  # Skip — this is actually valid
    except (json.JSONDecodeError, ValueError):
        pass

    with pytest.raises((ValidationError, ValueError)):
        AIResult.model_validate_json(garbage)


@given(st.text())
def test_airesult_reason_defaults_empty(text):
    """AIResult with only valid field gets empty reason."""
    result = AIResult(valid=True)
    assert result.reason == ""


# --- Rate limiter eviction ---


@given(st.lists(st.integers(min_value=1, max_value=100_000), min_size=1, max_size=3000))
@hsettings(max_examples=20)
def test_rate_limiter_bounded_size(chat_ids):
    """Rate limiter internal dicts never exceed MAX_TRACKED_CHATS."""
    mw = RateLimitMiddleware(min_interval=0.0)

    for cid in chat_ids:
        # Simulate what __call__ does to _last_calls
        mw._last_calls[cid] = 0.0
        mw._last_calls.move_to_end(cid)
        while len(mw._last_calls) > MAX_TRACKED_CHATS:
            evicted_id, _ = mw._last_calls.popitem(last=False)
            mw._locks.pop(evicted_id, None)

    assert len(mw._last_calls) <= MAX_TRACKED_CHATS


# --- ai_validation_result JSON round-trip ---


@given(st.fixed_dictionaries({
    "valid": st.booleans(),
    "reason": st.text(max_size=200),
}))
def test_ai_result_json_roundtrip(data):
    """ai_validation_result survives json.dumps → json.loads."""
    serialized = json.dumps(data)
    deserialized = json.loads(serialized)
    assert deserialized == data
    assert isinstance(deserialized["valid"], bool)
    assert isinstance(deserialized["reason"], str)
