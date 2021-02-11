from project.api import marshmallow
from marshmallow import fields, validate, missing


class SQLAlchemyBaseSchema(marshmallow.SQLAlchemySchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def make_post_schema(self):
        for name, field in self.fields.items():
            if not field.required:
                if field.missing is missing:
                    if isinstance(field, fields.List):
                        field.missing = list()
                    else:
                        field.missing = None
                field.allow_none = True

    def make_patch_schema(self):
        for name, field in self.fields.items():
            field.required = False
            field.allow_none = True


class IdSchemaMixin(object):
    id = marshmallow.auto_field(dump_only=True, default=missing)


class WriteIdSchemaMixin(object):
    id = marshmallow.auto_field(required=True)


class TrackableSchemaMixin(object):
    created_at = marshmallow.auto_field(dump_only=True)
    updated_at = marshmallow.auto_field(dump_only=True)


class ErrorResponseSchema(marshmallow.Schema):
    name = fields.Str()
    message = fields.Str()


class UnprocessableEntityErrorSchema(marshmallow.Schema):
    field = fields.Str()
    message = fields.Str()


class UnprocessableEntityResponseSchema(ErrorResponseSchema):
    errors = fields.List(fields.Nested(UnprocessableEntityErrorSchema))


class PaginationRequestSchema(marshmallow.Schema):
    page = fields.Integer(
        required=False,
        default=1,
        validate=validate.Range(min=1),
        metadata={"description": "The page number (1 indexed)."},
    )
    per_page = fields.Integer(
        required=False,
        default=20,
        validate=validate.Range(min=1, max=50),
        metadata={"description": "Items per page"},
    )


class PaginationResponseSchema(marshmallow.Schema):
    has_next = fields.Boolean(
        required=True, metadata={"description": "True if a next page exists."}
    )
    has_prev = fields.Boolean(
        required=True, metadata={"description": "True if a previous page exists."}
    )
    next_num = fields.Integer(
        required=False, metadata={"description": "Number of the next page."}
    )
    prev_num = fields.Integer(
        required=False, metadata={"description": "Number of the previous page."}
    )
    page = fields.Integer(
        required=True, metadata={"description": "The current page number (1 indexed)."}
    )
    pages = fields.Integer(
        required=True, metadata={"description": "The total number of pages."}
    )
    per_page = fields.Integer(required=True, metadata={"description": "Items per page"})
    total = fields.Integer(
        required=True,
        metadata={"description": "The total number of items matching the query"},
    )


class NoneSchema(marshmallow.Schema):
    pass
