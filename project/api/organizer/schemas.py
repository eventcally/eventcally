from project import marshmallow
from project.models import EventOrganizer


class OrganizerSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()


class OrganizerRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    href = marshmallow.URLFor(
        "organizerresource",
        values=dict(id="<id>"),
    )
