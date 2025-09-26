from marshmallow import fields

from project.api import marshmallow
from project.api.event.schemas import EventRefSchema, EventWriteIdSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)
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


class EventReferenceWriteSchemaMixin(object):
    event = fields.Nested(
        EventWriteIdSchema,
        required=True,
        metadata={"description": "Event to reference"},
    )


class EventReferenceCreateRequestSchema(
    EventReferenceModelSchema,
    EventReferenceWriteSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()
