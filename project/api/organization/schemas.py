from marshmallow import ValidationError, fields, post_dump, validate
from marshmallow.decorators import pre_load

from project.access import has_access, login_api_user
from project.api.image.schemas import ImageDumpSchema, ImageSchema
from project.api.location.schemas import (
    LocationDumpSchema,
    LocationSchema,
    LocationSearchItemSchema,
)
from project.api.schemas import (
    IdSchemaMixin,
    PaginationRequestSchema,
    PaginationResponseSchema,
    PlainBaseSchema,
    TrackableRequestSchemaMixin,
    TrackableSchemaMixin,
    WriteIdPlainSchema,
    WriteIdSchemaMixin,
)


class OrganizationModelSchema(PlainBaseSchema):
    pass


class OrganizationIdSchema(OrganizationModelSchema, IdSchemaMixin):
    pass


def _organization_exists(organization_id) -> bool:
    from flask import current_app

    from project.application.queries import GetOrganizationQuery

    query_bus = current_app.container.cqrs.query_bus()
    return query_bus.handle(GetOrganizationQuery(id=organization_id)) is not None


class OrganizationWriteIdSchema(OrganizationModelSchema, WriteIdSchemaMixin):
    def object_exists(self, object_id) -> bool:
        return _organization_exists(object_id)


class OrganizationWriteIdPlainSchema(WriteIdPlainSchema):
    @pre_load()
    def validate_exists(self, data, **kwargs):
        if not _organization_exists(data.get("id")):
            raise ValidationError("Referenced object does not exist")
        return data


class OrganizationBaseSchema(OrganizationIdSchema):
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
    name = fields.String(allow_none=True, validate=validate.Length(max=255))
    short_name = fields.String(allow_none=True, validate=validate.Length(max=100))
    url = fields.String(allow_none=True, validate=validate.Length(max=255))
    email = fields.String(allow_none=True, validate=validate.Length(max=255))
    phone = fields.String(allow_none=True, validate=validate.Length(max=255))
    fax = fields.String(allow_none=True, validate=validate.Length(max=255))
    description = fields.String(allow_none=True)
    is_verified = fields.Boolean()


class OrganizationSchema(OrganizationBaseSchema):
    location = fields.Nested(LocationSchema)
    logo = fields.Nested(ImageSchema)
    can_verify_other = fields.Boolean()
    incoming_reference_requests_allowed = fields.Boolean(allow_none=True)

    @post_dump(pass_original=True)
    def remove_private_fields(self, data, original_data, **kwargs):
        login_api_user()
        if not has_access(original_data, "settings:read"):
            data.pop("can_verify_other", None)
            data.pop("incoming_reference_requests_allowed", None)

        return data


class OrganizationDumpSchema(OrganizationBaseSchema):
    location = fields.Nested(LocationDumpSchema)
    logo = fields.Nested(ImageDumpSchema)


class OrganizationSearchItemSchema(OrganizationBaseSchema):
    location = fields.Nested(LocationSearchItemSchema)
    logo = fields.Nested(ImageSchema)


class OrganizationRefSchema(OrganizationIdSchema):
    name = fields.String(allow_none=True, validate=validate.Length(max=255))


class OrganizationListRefSchema(OrganizationRefSchema, TrackableSchemaMixin):
    short_name = fields.String(allow_none=True, validate=validate.Length(max=100))
    is_verified = fields.Boolean()


class OrganizationListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    keyword = fields.Str(
        metadata={"description": "Looks for keyword in name and short name."},
    )
    postal_code = fields.List(
        fields.Str(),
        metadata={"description": "Looks for organizations with this postal code."},
    )
    sort = fields.Str(
        metadata={"description": "Sort result items."},
        validate=validate.OneOf(
            ["-created_at", "-updated_at", "-last_modified_at", "name"]
        ),
    )


class OrganizationListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(OrganizationListRefSchema),
        metadata={"description": "Organizations"},
    )
