from marshmallow import fields, post_load

from project.api import marshmallow
from project.api.event.schemas import EventRefSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdPlainSchemaMixin,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
    WriteIdPlainSchema,
)
from project.application.commands import CreateEventReferenceCommand
from project.models import EventReference


class EventReferenceModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventReference
        load_instance = True


class EventReferenceIdSchema(EventReferenceModelSchema, IdSchemaMixin):
    pass


class EventReferenceRefSchema(EventReferenceIdSchema, TrackableSchemaMixin):
    event = fields.Nested(EventRefSchema)


class EventReferenceSchema(EventReferenceIdSchema):
    event = fields.Nested(EventRefSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class EventReferenceDumpSchema(EventReferenceIdSchema):
    event_id = marshmallow.auto_field()
    organization_id = fields.Int(attribute="admin_unit_id")


class EventReferenceListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    pass


class EventReferenceListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventReferenceRefSchema),
        metadata={"description": "Event references"},
    )


class EventReferenceIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class EventReferenceCreateRequestPlainSchema(PlainBaseSchema):
    event = fields.Nested(
        WriteIdPlainSchema,
        attribute="event_id",
        required=True,
        metadata={"description": "Event to reference"},
    )

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return CreateEventReferenceCommand(**data)
