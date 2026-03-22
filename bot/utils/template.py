from __future__ import annotations


def render(template: str, **kwargs) -> str:
    """Render a template string with {key} placeholders."""
    result = template
    for key, value in kwargs.items():
        result = result.replace("{" + key + "}", str(value))
    return result
