from marshmallow import fields
from project import marshmallow
from project.models import EventOrganizer
from project.api.location.schemas import LocationRefSchema
from project.api.image.schemas import ImageRefSchema
from project.api.organization.schemas import OrganizationRefSchema


class OrganizerSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    email = marshmallow.auto_field()
    phone = marshmallow.auto_field()
    fax = marshmallow.auto_field()
    location = fields.Nested(LocationRefSchema)
    logo = fields.Nested(ImageRefSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class OrganizerRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventOrganizer

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    href = marshmallow.URLFor(
        "organizerresource",
        values=dict(id="<id>"),
    )
