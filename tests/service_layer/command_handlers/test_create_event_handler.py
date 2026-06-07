from datetime import datetime, timezone

from project.application import commands
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.models import Event


def test_create_event_command_creates_event(app, db, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        message_bus = app.container.cqrs.message_bus()
        cmd = commands.CreateEventCommand.model_construct(
            admin_unit_id=admin_unit_id,
            name="Test Event",
            organizer_id=organizer_id,
            event_place_id=place_id,
            date_definitions=[
                EventDateDefinitionValueObject(start=datetime.now(timezone.utc))
            ],
        )

        result = message_bus.handle_command(cmd)

        event = db.session.get(Event, result.id)
        assert event is not None
        assert event.name == "Test Event"
        assert event.admin_unit_id == admin_unit_id
        assert event.organizer_id == organizer_id
        assert event.event_place_id == place_id
        assert len(event.date_definitions) == 1
