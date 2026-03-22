from bot.utils.template import render


def test_render_basic():
    result = render("Hello {name}!", name="World")
    assert result == "Hello World!"


def test_render_multiple():
    result = render("{a} and {b}", a="X", b="Y")
    assert result == "X and Y"


def test_render_timeout():
    tpl = "Представьтесь в течение {timeout} минут."
    result = render(tpl, timeout=15)
    assert result == "Представьтесь в течение 15 минут."


def test_render_no_placeholders():
    result = render("No placeholders here")
    assert result == "No placeholders here"


def test_render_missing_key():
    result = render("{missing} stays", other="val")
    assert result == "{missing} stays"
