from marshmallow import fields
from project import marshmallow
from project.models import EventPlace
from project.api.image.schemas import ImageRefSchema
from project.api.location.schemas import LocationRefSchema, LocationSearchItemSchema
from project.api.organization.schemas import OrganizationRefSchema
from project.api.schemas import PaginationRequestSchema, PaginationResponseSchema


class PlaceIdSchema(marshmallow.SQLAlchemySchema):
    class Meta:
        model = EventPlace

    id = marshmallow.auto_field()


class PlaceBaseSchema(PlaceIdSchema):
    created_at = marshmallow.auto_field()
    updated_at = marshmallow.auto_field()
    name = marshmallow.auto_field()
    url = marshmallow.auto_field()
    description = marshmallow.auto_field()


class PlaceSchema(PlaceBaseSchema):
    location = fields.Nested(LocationRefSchema)
    photo = fields.Nested(ImageRefSchema)
    organization = fields.Nested(OrganizationRefSchema, attribute="adminunit")


class PlaceDumpSchema(PlaceBaseSchema):
    location_id = fields.Int()
    photo_id = fields.Int()
    organization_id = fields.Int(attribute="admin_unit_id")


class PlaceRefSchema(PlaceIdSchema):
    name = marshmallow.auto_field()


class PlaceSearchItemSchema(PlaceRefSchema):
    class Meta:
        model = EventPlace

    location = fields.Nested(LocationSearchItemSchema)


class PlaceListRequestSchema(PaginationRequestSchema):
    name = fields.Str(
        metadata={"description": "Looks for name."},
    )


class PlaceListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(PlaceRefSchema), metadata={"description": "Places"}
    )
