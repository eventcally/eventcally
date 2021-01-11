from project import marshmallow
from project.models import EventCategory


class EventCategoryRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventCategory

    name = marshmallow.auto_field()
