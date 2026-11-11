from marshmallow import fields, post_load, validate

from project.application.commands import (
    AddEventToCalendarCommand,
    CreateCalendarCommand,
    UpdateCalendarCommand,
)
from project.presentation.api.organization.schemas import OrganizationRefSchema
from project.presentation.api.schemas import (
    IdPlainSchemaMixin,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
)


class CalendarModelSchema(PlainBaseSchema):
    pass


class CalendarIdSchema(CalendarModelSchema, IdSchemaMixin):
    pass


class CalendarIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class CalendarBaseSchemaMixin(TrackableSchemaMixin):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str()
    private = fields.Bool(
        metadata={
            "description": "Private calendars have no public page and cannot be "
            "used as search filter by others."
        }
    )


class CalendarSchema(CalendarIdSchema, CalendarBaseSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class CalendarRefSchema(CalendarIdSchema):
    name = fields.String(required=True, validate=validate.Length(max=255))


class CalendarListRefSchema(CalendarRefSchema, TrackableSchemaMixin):
    description = fields.Str()
    private = fields.Bool()
    number_of_events = fields.Int()


class CalendarListRequestSchema(PaginationRequestSchema, TrackableRequestSchemaMixin):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            [
                "-created_at",
                "-updated_at",
                "-last_modified_at",
                "-number_of_events",
                "name",
            ]
        ),
    )


class CalendarListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(CalendarListRefSchema), metadata={"description": "Calendars"}
    )


class CalendarCreateRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default=None)
    private = fields.Bool(load_default=False)

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return CreateCalendarCommand(**data)


class CalendarPutRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(load_default=None)
    private = fields.Bool(load_default=False)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateCalendarCommand(**data)


class CalendarPatchRequestPlainSchema(PlainBaseSchema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    private = fields.Bool()

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateCalendarCommand(**data)


class CalendarEventAddRequestPlainSchema(PlainBaseSchema):
    event_id = fields.Int(required=True)

    @post_load
    def make_instance(self, data, **kwargs):
        data["calendar_id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return AddEventToCalendarCommand(**data)
