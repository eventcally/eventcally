from marshmallow import fields

from project.api import marshmallow
from project.api.custom_event_category_set.schemas import (
    CustomEventCategorySetRefSchema,
)
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
    WriteIdSchemaMixin,
)
from project.models import CustomEventCategory


class CustomEventCategoryModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = CustomEventCategory
        load_instance = True


class CustomEventCategoryIdSchema(CustomEventCategoryModelSchema, IdSchemaMixin):
    pass


class CustomEventCategoryRefSchema(CustomEventCategoryIdSchema):
    name = marshmallow.auto_field()
    label = marshmallow.auto_field()
    category_set = fields.Nested(CustomEventCategorySetRefSchema)


class CustomEventCategoryWriteIdSchema(
    CustomEventCategoryModelSchema, WriteIdSchemaMixin
):
    pass


class CustomEventCategoryDumpSchema(CustomEventCategoryRefSchema):
    pass


class CustomEventCategoryListRequestSchema(PaginationRequestSchema):
    pass


class CustomEventCategoryListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(CustomEventCategoryRefSchema),
        metadata={"description": "Custom event categories"},
    )
