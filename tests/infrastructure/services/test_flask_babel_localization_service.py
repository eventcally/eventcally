def test_get_text(app):
    with app.app_context():
        from project.infrastructure.services.flask_babel_localization_service import (
            FlaskBabelLocalizationService,
        )

        service = FlaskBabelLocalizationService()
        result = service.get_text("key")
        assert result is not None
