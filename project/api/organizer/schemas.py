from project import marshmallow
from project.models import EventOrganizer


class OrganizerSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
