from project import marshmallow
from project.models import AdminUnit


class OrganizationSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = AdminUnit

    id = marshmallow.auto_field()
    name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    email = marshmallow.auto_field()
    phone = marshmallow.auto_field()
    fax = marshmallow.auto_field()
