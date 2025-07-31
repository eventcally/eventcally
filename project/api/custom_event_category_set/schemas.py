from marshmallow import fields

from project.api import marshmallow
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    SQLAlchemyBaseSchema,
)
from project.models import CustomEventCategorySet


class CustomEventCategorySetModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = CustomEventCategorySet
        load_instance = True


class CustomEventCategorySetIdSchema(CustomEventCategorySetModelSchema, IdSchemaMixin):
    pass


class CustomEventCategorySetRefSchema(CustomEventCategorySetIdSchema):
    name = marshmallow.auto_field()
    label = marshmallow.auto_field()


class CustomEventCategorySetDumpSchema(CustomEventCategorySetRefSchema):
    pass


class CustomEventCategorySetListRequestSchema(PaginationRequestSchema):
    pass


class CustomEventCategorySetListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(CustomEventCategorySetRefSchema),
        metadata={"description": "Custom event category sets"},
    )
