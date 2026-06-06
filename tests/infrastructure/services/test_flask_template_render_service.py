def test_render_template(app):
    with app.app_context():
        from project.infrastructure.services.flask_template_render_service import (
            FlaskTemplateRenderService,
        )

        report = {
            "contact_name": "John Doe",
            "contact_email": "john.doe@example.com",
            "message": "This is a sample event report.",
        }
        event = {"id": 1}

        service = FlaskTemplateRenderService()
        result = service.render_template(
            "email/event_report_notice.txt", report=report, event=event
        )
        assert "John Doe" in result
