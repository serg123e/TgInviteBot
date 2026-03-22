from __future__ import annotations

from html import escape


def render(template: str, **kwargs) -> str:
    """Render a template string with {key} placeholders."""
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result


def user_display(
    username: str | None, first_name: str | None, user_id: int
) -> str:
    """Format a user mention: @username, first_name (id: N), or id: N."""
    if username:
        return f"@{escape(username)}"
    if first_name:
        return f"{escape(first_name)} (id: {user_id})"
    return f"id: {user_id}"
