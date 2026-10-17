from datetime import datetime, timezone


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


def _referenced_event_changed_context():
    from project.application.read_models.event_change_summary_read_model import (
        EventChangeSummaryReadModel,
    )
    from project.application.read_models.event_read_model import (
        AdminUnitReadModel,
        EventDateDefinitionReadModel,
        EventReadModel,
        OrganizerReadModel,
    )
    from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
    from project.domain.models.enums.event_status import EventStatus
    from project.domain.types.changed_value import ChangedValue

    event = EventReadModel(
        id=1,
        name="New Name",
        is_recurring=False,
        admin_unit=AdminUnitReadModel(id=1, name="Organization"),
        organizer=OrganizerReadModel(id=2, name="New Organizer"),
        min_start_definition=EventDateDefinitionReadModel(
            start=datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc)
        ),
    )
    changes = EventChangeSummaryReadModel(
        name=ChangedValue(old="Old Name", new="New Name"),
        status=ChangedValue(old=EventStatus.scheduled, new=EventStatus.cancelled),
        attendance_mode=ChangedValue(
            old=EventAttendanceMode.online, new=EventAttendanceMode.offline
        ),
        booked_up=ChangedValue(old=None, new=True),
        organizer=ChangedValue(old=None, new="New Organizer"),
        event_place=ChangedValue(old="Old Place", new="New Place"),
        date_definitions=ChangedValue(
            old=[
                EventDateDefinitionReadModel(
                    start=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
                )
            ],
            new=[
                EventDateDefinitionReadModel(
                    start=datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc)
                ),
                EventDateDefinitionReadModel(
                    start=datetime(2026, 2, 8, 10, 0, tzinfo=timezone.utc),
                    recurrence_rule="RRULE:FREQ=WEEKLY",
                ),
            ],
        ),
    )

    class _Reference:
        id = 7
        admin_unit_id = 1

    return {"event": event, "reference": _Reference(), "changes": changes}


def test_render_referenced_event_changed_notice_with_changes(app):
    with app.app_context():
        from project.infrastructure.services.flask_template_render_service import (
            FlaskTemplateRenderService,
        )

        service = FlaskTemplateRenderService()
        context = _referenced_event_changed_context()

        body = service.render_template_with_locale(
            "en", "email/referenced_event_changed_notice.txt", **context
        )
        html = service.render_template_with_locale(
            "en", "email/referenced_event_changed_notice.html", **context
        )

    for result in (body, html):
        assert "What changed" in result
        # Names, not ids
        assert "Old Place -> New Place" in result or "Old Place" in result
        assert "New Organizer" in result
        # A deleted / unset old side renders as a placeholder, never as None
        assert "None" not in result
        # Enums and booleans are translated, not dumped
        assert "EventStatus.cancelled" not in str(result)
        # Full date lists, old and new
        assert "Dates (previously)" in result
        assert "Dates (new)" in result

    # The plain text variant must not leak markup from the shared macros
    assert "<ul>" not in body
    assert "<li>" not in body


def test_render_referenced_event_changed_notice_without_changes(app):
    with app.app_context():
        from project.infrastructure.services.flask_template_render_service import (
            FlaskTemplateRenderService,
        )

        service = FlaskTemplateRenderService()
        context = _referenced_event_changed_context()
        context["changes"] = None

        body = service.render_template_with_locale(
            "en", "email/referenced_event_changed_notice.txt", **context
        )
        html = service.render_template_with_locale(
            "en", "email/referenced_event_changed_notice.html", **context
        )

    for result in (body, html):
        assert "A referenced event was changed." in result
        assert "What changed" not in result
