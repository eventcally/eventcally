from marshmallow import fields
from project.api import marshmallow
from project.models import EventReference
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema
from project.api.event.schemas import EventRefSchema
from project.api.organization.schemas import OrganizationRefSchema


class EventReferenceIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventReference
        load_instance = True

    id = marshmallow.auto_field()


class EventReferenceRefSchema(EventReferenceIdSchema):
    event = fields.Nested(EventRefSchema)


class EventReferenceSchema(EventReferenceIdSchema):
    event = fields.Nested(EventRefSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class EventReferenceDumpSchema(EventReferenceIdSchema):
    event_id = marshmallow.auto_field()
    organization_id = fields.Int(attribute="admin_unit_id")


class EventReferenceListRequestSchema(PaginationRequestSchema):
    pass


class EventReferenceListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventReferenceRefSchema),
        metadata={"description": "Event references"},
    )
