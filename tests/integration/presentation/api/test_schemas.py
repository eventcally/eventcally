import pytest


def test_write_id_schema_mixin_raises_on_unknown_reference(app, db):
    from marshmallow import ValidationError

    from project.presentation.api.event.schemas import EventWriteIdSchema

    with app.app_context():
        with pytest.raises(ValidationError):
            EventWriteIdSchema().load({"id": 999999})


def test_write_id_schema_mixin_on_plain_schemas_uses_object_exists(app):
    from marshmallow import ValidationError

    from project.presentation.api.schemas import PlainBaseSchema, WriteIdSchemaMixin

    class KnownIdSchema(PlainBaseSchema, WriteIdSchemaMixin):
        def object_exists(self, object_id):
            return object_id == 1

    assert KnownIdSchema().load({"id": 1}) == {"id": 1}

    with pytest.raises(ValidationError):
        KnownIdSchema().load({"id": 2})


def test_event_write_id_schemas_check_the_event(app, db, seeder):
    from marshmallow import ValidationError

    from project.presentation.api.event.schemas import (
        EventWriteIdPlainSchema,
        EventWriteIdSchema,
    )

    _, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        assert EventWriteIdSchema().load({"id": event_id}) == {"id": event_id}
        EventWriteIdPlainSchema().load({"id": event_id})

        for schema in (EventWriteIdSchema(), EventWriteIdPlainSchema()):
            for invalid in (4711, "abc", None):
                with pytest.raises(ValidationError):
                    schema.load({"id": invalid})


def test_organization_write_id_schema_checks_the_organization(app, db, seeder):
    from marshmallow import ValidationError

    from project.presentation.api.organization.schemas import OrganizationWriteIdSchema

    _, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        assert OrganizationWriteIdSchema().load({"id": admin_unit_id})["id"] == (
            admin_unit_id
        )

        with pytest.raises(ValidationError):
            OrganizationWriteIdSchema().load({"id": 4711})
