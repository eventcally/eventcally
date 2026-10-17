from typing import Optional

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.event_ref_read_model import EventRefReadModel
from project.application.read_models.image_read_model import (
    ImageEditReadModel,
    ImageReadModel,
    LicenseRefReadModel,
)
from project.application.read_models.location_read_model import LocationReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)


def to_location_read_model(location) -> Optional[LocationReadModel]:
    if location is None:
        return None

    return LocationReadModel(
        street=location.street,
        postalCode=location.postalCode,
        city=location.city,
        state=location.state,
        country=location.country,
        latitude=location.latitude,
        longitude=location.longitude,
    )


def to_image_read_model(image) -> Optional[ImageReadModel]:
    if image is None:
        return None

    return ImageReadModel(
        id=image.id,
        copyright_text=image.copyright_text,
        last_modified_at=image.last_modified_at,
        license=_to_license_ref(image.license),
    )


def to_image_edit_read_model(image) -> Optional[ImageEditReadModel]:
    """Needs `Image.data` undeferred."""
    if image is None:
        return None

    return ImageEditReadModel(
        id=image.id,
        data=image.data,
        encoding_format=image.encoding_format,
        copyright_text=image.copyright_text,
        license=_to_license_ref(image.license),
    )


def _to_license_ref(license) -> Optional[LicenseRefReadModel]:
    if license is None:
        return None

    return LicenseRefReadModel(
        id=license.id, name=license.name, code=license.code, url=license.url
    )


def to_organization_ref_read_model(admin_unit) -> OrganizationRefReadModel:
    return OrganizationRefReadModel(id=admin_unit.id, name=admin_unit.name)


def to_event_ref_read_model(event) -> EventRefReadModel:
    """Needs `event.admin_unit` loaded."""
    return EventRefReadModel(
        id=event.id,
        name=event.name,
        admin_unit=to_organization_ref_read_model(event.admin_unit),
    )


def audit_options(model) -> list:
    """Eager loads for `to_audit_read_model` on a `TrackableMixin` model."""
    from sqlalchemy.orm import joinedload, undefer_group

    from project.infrastructure.models import AppInstallation, OAuth2Client, User

    def installation(relationship):
        return (
            joinedload(relationship)
            .load_only(AppInstallation.id, AppInstallation.oauth2_client_id)
            .joinedload(AppInstallation.oauth2_client)
            .load_only(OAuth2Client.id, OAuth2Client._client_metadata)
        )

    return [
        undefer_group("trackable"),
        joinedload(model.created_by).load_only(User.id, User.email),
        joinedload(model.updated_by).load_only(User.id, User.email),
        installation(model.created_by_app_installation),
        installation(model.updated_by_app_installation),
    ]


def to_audit_read_model(trackable) -> AuditReadModel:
    """Needs `audit_options` loaded; mirrors `TrackableMixin.created_by_label`."""
    return AuditReadModel(
        created_at=trackable.created_at,
        updated_at=trackable.updated_at,
        created_by_label=_actor_label(
            trackable.created_by, trackable.created_by_app_installation
        ),
        updated_by_label=_actor_label(
            trackable.updated_by, trackable.updated_by_app_installation
        ),
    )


def _actor_label(user, app_installation) -> Optional[str]:
    if user:
        return user.email

    if app_installation:
        return app_installation.oauth2_client.client_name

    return None


def to_organization_member_read_model(member):
    """Needs `member.user` and `member.roles` loaded; roles ordered by id."""
    from project.application.read_models.organization_member_read_models import (
        OrganizationMemberReadModel,
        OrganizationMemberRoleReadModel,
    )
    from project.application.read_models.user_ref_read_model import UserRefReadModel

    return OrganizationMemberReadModel(
        id=member.id,
        admin_unit_id=member.admin_unit_id,
        user_id=member.user_id,
        user=UserRefReadModel(id=member.user.id, email=member.user.email),
        roles=[
            OrganizationMemberRoleReadModel(
                id=role.id, name=role.name, title=role.title
            )
            for role in sorted(member.roles, key=lambda r: r.id)
        ],
    )
