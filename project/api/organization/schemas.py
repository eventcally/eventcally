from marshmallow import fields
from project import marshmallow
from project.models import AdminUnit
from project.api.location.schemas import LocationRefSchema
from project.api.image.schemas import ImageRefSchema


class OrganizationSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = AdminUnit

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    short_name = marshmallow.auto_field()
    location = fields.Nested(LocationRefSchema)
    logo = fields.Nested(ImageRefSchema)
    url = marshmallow.auto_field()
    email = marshmallow.auto_field()
    phone = marshmallow.auto_field()
    fax = marshmallow.auto_field()


class OrganizationRefSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = AdminUnit

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    href = marshmallow.URLFor("organizationresource", values=dict(id="<id>"))
