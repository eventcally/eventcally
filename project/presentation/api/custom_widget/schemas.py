from marshmallow import fields, post_load, validate

from project.application.commands import (
    CreateCustomWidgetCommand,
    UpdateCustomWidgetCommand,
)
from project.presentation.api.organization.schemas import OrganizationRefSchema
from project.presentation.api.schemas import (
    IdPlainSchemaMixin,
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    TrackableSchemaMixin,
    WriteIdSchemaMixin,
)


class CustomWidgetModelSchema(PlainBaseSchema):
    pass


class CustomWidgetIdSchema(CustomWidgetModelSchema, IdSchemaMixin):
    pass


class CustomWidgetIdPlainSchema(PlainBaseSchema, IdPlainSchemaMixin):
    pass


class CustomWidgetDumpIdSchema(CustomWidgetModelSchema, IdSchemaMixin):
    pass


class CustomWidgetWriteIdSchema(CustomWidgetModelSchema, WriteIdSchemaMixin):
    pass


class CustomWidgetBaseSchemaMixin(TrackableSchemaMixin):
    widget_type = fields.String(required=True, validate=validate.Length(min=3, max=255))
    name = fields.String(required=True, validate=validate.Length(min=3, max=255))
    settings = fields.Dict(keys=fields.Str())


class CustomWidgetSchema(CustomWidgetIdSchema, CustomWidgetBaseSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class CustomWidgetDumpSchema(CustomWidgetIdSchema, CustomWidgetBaseSchemaMixin):
    organization_id = fields.Int(attribute="admin_unit_id")


class CustomWidgetRefSchema(CustomWidgetIdSchema):
    widget_type = fields.String(required=True, validate=validate.Length(max=255))
    name = fields.String(required=True, validate=validate.Length(max=255))


class CustomWidgetListRequestSchema(PaginationRequestSchema):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )


class CustomWidgetListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(CustomWidgetRefSchema), metadata={"description": "Custom widgets"}
    )


class CustomWidgetPostRequestSchema(
    CustomWidgetModelSchema, CustomWidgetBaseSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_post_schema()


class CustomWidgetPatchRequestSchema(
    CustomWidgetModelSchema, CustomWidgetBaseSchemaMixin
):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.make_patch_schema()


class CustomWidgetCreateRequestPlainSchema(PlainBaseSchema):
    widget_type = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    settings = fields.Dict(keys=fields.Str(), load_default=None)

    @post_load
    def make_instance(self, data, **kwargs):
        data["admin_unit_id"] = self.context.get("admin_unit_id")
        data["actor"] = self.context.get("actor")
        return CreateCustomWidgetCommand(**data)


class CustomWidgetPutRequestPlainSchema(PlainBaseSchema):
    widget_type = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    name = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    settings = fields.Dict(keys=fields.Str(), load_default=None)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateCustomWidgetCommand(**data)


class CustomWidgetPatchRequestPlainSchema(PlainBaseSchema):
    widget_type = fields.Str(allow_none=True, validate=validate.Length(min=3, max=255))
    name = fields.Str(allow_none=True, validate=validate.Length(min=3, max=255))
    settings = fields.Dict(keys=fields.Str(), allow_none=True)

    @post_load
    def make_instance(self, data, **kwargs):
        data["id"] = self.context.get("id")
        data["actor"] = self.context.get("actor")
        return UpdateCustomWidgetCommand(**data)
