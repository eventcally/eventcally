def test_get_text(app):
    with app.app_context():
        from project.infrastructure.services.flask_babel_localization_service import (
            FlaskBabelLocalizationService,
        )

        service = FlaskBabelLocalizationService()
        result = service.get_text("key")
        assert result is not None


def test_get_text_with_locale_translates_in_the_given_locale(app):
    from project.infrastructure.services.flask_babel_localization_service import (
        FlaskBabelLocalizationService,
    )

    with app.test_request_context():
        service = FlaskBabelLocalizationService()

        assert service.get_text_with_locale("de", "Event") == "Veranstaltung"
        assert service.get_text_with_locale("en", "Event") == "Event"
