def test_dynamic_texts(client, app, utils):
    from project.i10n import print_dynamic_texts

    print_dynamic_texts()


def test_get_locale_without_request_context(app):
    """Covers i10n.py line 19: returns BABEL_DEFAULT_LOCALE when no request context."""
    with app.app_context():
        from project.i10n import get_locale

        locale = get_locale()
        assert locale == app.config["BABEL_DEFAULT_LOCALE"]
