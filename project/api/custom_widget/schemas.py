from marshmallow import fields, validate

from project.api import marshmallow
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    TrackableSchemaMixin,
    WriteIdSchemaMixin,
)
from project.models import CustomWidget


class CustomWidgetModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = CustomWidget
        load_instance = True


class CustomWidgetIdSchema(CustomWidgetModelSchema, IdSchemaMixin):
    pass


class CustomWidgetDumpIdSchema(CustomWidgetModelSchema, IdSchemaMixin):
    pass


class CustomWidgetWriteIdSchema(CustomWidgetModelSchema, WriteIdSchemaMixin):
    pass


class CustomWidgetBaseSchemaMixin(TrackableSchemaMixin):
    widget_type = marshmallow.auto_field(
        required=True, validate=validate.Length(min=3, max=255)
    )
    name = marshmallow.auto_field(
        required=True, validate=validate.Length(min=3, max=255)
    )
    settings = fields.Dict(keys=fields.Str())


class CustomWidgetSchema(CustomWidgetIdSchema, CustomWidgetBaseSchemaMixin):
    organization = fields.Nested(OrganizationRefSchema, attribute="admin_unit")


class CustomWidgetDumpSchema(CustomWidgetIdSchema, CustomWidgetBaseSchemaMixin):
    organization_id = fields.Int(attribute="admin_unit_id")


class CustomWidgetRefSchema(CustomWidgetIdSchema):
    widget_type = marshmallow.auto_field()
    name = marshmallow.auto_field()


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
