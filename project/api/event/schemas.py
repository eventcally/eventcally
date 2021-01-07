from project import marshmallow
from marshmallow import fields
from project.models import Event


class EventSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    description = marshmallow.auto_field()
    external_link = marshmallow.auto_field()
    ticket_link = marshmallow.auto_field()
    tags = marshmallow.auto_field()
    kid_friendly = marshmallow.auto_field()
    accessible_for_free = marshmallow.auto_field()
    age_from = marshmallow.auto_field()
    age_to = marshmallow.auto_field()

    organization = marshmallow.HyperlinkRelated(
        "organizationresource", attribute="admin_unit"
    )
    organizer = marshmallow.URLFor(
        "organizerresource",
        values=dict(organization_id="<admin_unit_id>", organizer_id="<organizer_id>"),
    )


class EventListItemSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = Event

    id = marshmallow.auto_field()
    href = marshmallow.URLFor("eventresource", values=dict(id="<id>"))
    name = marshmallow.auto_field()
    start = marshmallow.auto_field()
    end = marshmallow.auto_field()
    recurrence_rule = marshmallow.auto_field()


class EventListRequestSchema(marshmallow.Schema):
    page = fields.Integer(
        required=False,
        default=1,
        metadata={"description": "The page number (1 indexed)."},
    )
    per_page = fields.Integer(
        required=False, default=20, metadata={"description": "Items per page"}
    )


class EventListResponseSchema(marshmallow.Schema):
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
    items = fields.List(
        fields.Nested(EventListItemSchema), metadata={"description": "Events"}
    )
