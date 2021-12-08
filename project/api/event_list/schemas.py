from marshmallow import fields, pre_dump, validate

from project.api import marshmallow
from project.api.event.schemas import EventWriteIdSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableSchemaMixin,
    WriteIdSchemaMixin,
)
from project.models import EventList


class EventListModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventList
        load_instance = True


class EventListIdSchema(EventListModelSchema, IdSchemaMixin):
    pass


class EventListWriteIdSchema(EventListModelSchema, WriteIdSchemaMixin):
    pass


class EventListBaseSchemaMixin(TrackableSchemaMixin):
    name = marshmallow.auto_field(
        required=True, validate=validate.Length(min=3, max=255)
    )


class EventListSchema(EventListIdSchema, EventListBaseSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class EventListRefSchema(EventListIdSchema):
    name = marshmallow.auto_field()


class EventListListRequestSchema(PaginationRequestSchema):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )


class EventListListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventListRefSchema), metadata={"description": "Event lists"}
    )


class EventListStatusSchema(marshmallow.Schema):
    event_list = fields.Nested(EventListRefSchema)
    contains_event = fields.Boolean(
        required=True, metadata={"description": "True if list contains event."}
    )

    @pre_dump(pass_many=True)
    def unwrap_tuple(self, data, many, **kwargs):
        return {"event_list": data[0], "contains_event": data[1] > 0}


class EventListStatusListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(EventListStatusSchema),
        metadata={"description": "Event list stati"},
    )


class EventListWriteSchemaMixin(object):
    pass


class EventListCreateRequestSchema(
    EventListModelSchema,
    EventListBaseSchemaMixin,
    EventListWriteSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class EventListUpdateRequestSchema(
    EventListModelSchema,
    EventListBaseSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class EventListPatchRequestSchema(
    EventListModelSchema,
    EventListBaseSchemaMixin,
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()


class EventListEventRequestSchema(marshmallow.Schema):
    event = fields.Nested(
        EventWriteIdSchema,
        required=True,
        metadata={"description": "Event."},
    )
