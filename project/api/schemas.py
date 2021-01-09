from project import marshmallow
from marshmallow import fields


class PaginationRequestSchema(marshmallow.Schema):
    page = fields.Integer(
        required=False,
        default=1,
        metadata={"description": "The page number (1 indexed)."},
    )
    per_page = fields.Integer(
        required=False, default=20, metadata={"description": "Items per page"}
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
