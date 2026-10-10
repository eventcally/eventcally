from project.domain.translation import dummy_gettext


def test_dummy_gettext_returns_message_unchanged():
    assert dummy_gettext("x") == "x"
