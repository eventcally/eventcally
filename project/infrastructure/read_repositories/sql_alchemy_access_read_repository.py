from typing import List, Optional

from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import joinedload, selectinload, undefer, undefer_group

from project.application.queries.get_resource_owner_query import ResourceKind
from project.application.read_models.access_helper_read_models import (
    MailRecipientReadModel,
    ManageMenuOptionsReadModel,
    MemberGrantsReadModel,
)
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.application.read_models.current_organization_read_models import (
    CurrentOrganizationReadModel,
    OrganizationSettingsReadModel,
)
from project.application.read_models.location_read_model import LocationReadModel
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    AdminUnitInvitation,
    AdminUnitMember,
    AdminUnitMemberRole,
    AdminUnitRelation,
    AdminUnitVerificationRequest,
    AdminUnitVerificationRequestReviewStatus,
    ApiKey,
    CustomWidget,
    Event,
    EventOrganizer,
    EventPlace,
    EventReference,
    EventReferenceRequest,
    EventReferenceRequestReviewStatus,
    Image,
    Location,
    Role,
    User,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    to_image_edit_read_model,
    to_location_read_model,
)

_ORGANIZATION_COLUMNS = (
    AdminUnit.id,
    AdminUnit.name,
    AdminUnit.short_name,
    AdminUnit.can_verify_other,
    AdminUnit.can_invite_other,
    AdminUnit.can_create_other,
    AdminUnit.incoming_reference_requests_allowed,
    AdminUnit.incoming_verification_requests_allowed,
    AdminUnit.is_verified,
    AdminUnit.location_id,
    Location.street,
    Location.postalCode,
    Location.city,
    Location.state,
    Location.country,
    Location.latitude,
    Location.longitude,
)


class SqlAlchemyAccessReadRepository(AbstractAccessReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def get_organization(
        self, admin_unit_id: ObjectId
    ) -> Optional[CurrentOrganizationReadModel]:
        row = self.session.execute(
            select(*_ORGANIZATION_COLUMNS)
            .outerjoin(Location, Location.id == AdminUnit.location_id)
            .where(AdminUnit.id == admin_unit_id)
        ).one_or_none()
        return _to_organization(row) if row else None

    def list_organizations(
        self, admin_unit_ids: Optional[List[ObjectId]]
    ) -> List[CurrentOrganizationReadModel]:
        stmt = select(*_ORGANIZATION_COLUMNS).outerjoin(
            Location, Location.id == AdminUnit.location_id
        )

        if admin_unit_ids is not None:
            stmt = stmt.where(AdminUnit.id.in_(admin_unit_ids))

        rows = self.session.execute(stmt.order_by(AdminUnit.id)).all()
        organizations = [_to_organization(row) for row in rows]

        if admin_unit_ids is None:
            return organizations

        by_id = {organization.id: organization for organization in organizations}
        return [by_id[i] for i in admin_unit_ids if i in by_id]

    def member_organization_ids(self, user_id: ObjectId) -> List[ObjectId]:
        return list(
            self.session.execute(
                select(AdminUnitMember.admin_unit_id)
                .where(AdminUnitMember.user_id == user_id)
                .order_by(AdminUnitMember.id)
            ).scalars()
        )

    def get_resource_owner(
        self, kind: ResourceKind, resource_id: ObjectId
    ) -> Optional[ObjectId]:
        if kind == ResourceKind.event_reference_request:
            stmt = (
                select(Event.admin_unit_id)
                .join(EventReferenceRequest, EventReferenceRequest.event_id == Event.id)
                .where(EventReferenceRequest.id == resource_id)
            )
        else:
            model, column = _OWNER_COLUMNS[kind]
            stmt = select(column).where(model.id == resource_id)

        return self.session.execute(stmt).scalar_one_or_none()

    def has_other_admin(self, admin_unit_id: ObjectId, user_id: ObjectId) -> bool:
        return self.session.execute(
            select(
                exists().where(
                    AdminUnitMember.user_id != user_id,
                    AdminUnitMember.admin_unit_id == admin_unit_id,
                    AdminUnitMember.roles.any(AdminUnitMemberRole.name == "admin"),
                )
            )
        ).scalar_one()

    def is_name_taken(self, name: str, exclude_id: Optional[ObjectId]) -> bool:
        return self._taken(func.lower(AdminUnit.name) == name.lower(), exclude_id)

    def is_short_name_taken(
        self, short_name: str, exclude_id: Optional[ObjectId]
    ) -> bool:
        return self._taken(
            func.lower(AdminUnit.short_name) == short_name.lower(), exclude_id
        )

    def _taken(self, condition, exclude_id: Optional[ObjectId]) -> bool:
        filters = [condition]

        if exclude_id is not None:
            filters.append(AdminUnit.id != exclude_id)

        return self.session.execute(select(exists().where(*filters))).scalar_one()

    def can_request_verification(
        self, source_admin_unit_id: ObjectId, target_admin_unit_id: ObjectId
    ) -> bool:
        postal_code = self.session.execute(
            select(Location.postalCode)
            .join(AdminUnit, AdminUnit.location_id == Location.id)
            .where(AdminUnit.id == source_admin_unit_id)
        ).scalar_one_or_none()

        return self.session.execute(
            select(
                exists().where(
                    AdminUnit.id == target_admin_unit_id,
                    AdminUnit.id != source_admin_unit_id,
                    AdminUnit.can_verify_other,
                    AdminUnit.incoming_verification_requests_allowed,
                    or_(
                        AdminUnit.incoming_verification_requests_postal_codes == "{}",
                        AdminUnit.incoming_verification_requests_postal_codes.contains(
                            [postal_code]
                        ),
                    ),
                )
            )
        ).scalar_one()

    def any_accepts_reference_requests(self, exclude_admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(
                exists().where(
                    AdminUnit.id != exclude_admin_unit_id,
                    AdminUnit.incoming_reference_requests_allowed,
                )
            )
        ).scalar_one()

    def get_settings(
        self, admin_unit_id: ObjectId
    ) -> Optional[OrganizationSettingsReadModel]:
        admin_unit = self.session.execute(
            select(AdminUnit)
            .where(AdminUnit.id == admin_unit_id)
            .options(
                undefer(AdminUnit.logo_id),
                undefer_group("detail"),
                undefer_group("widget"),
                undefer_group("deletion"),
                undefer(AdminUnit.incoming_verification_requests_allowed),
                undefer(AdminUnit.incoming_verification_requests_text),
                undefer(AdminUnit.incoming_verification_requests_postal_codes),
                joinedload(AdminUnit.location),
                joinedload(AdminUnit.logo).options(
                    undefer(Image.data), joinedload(Image.license)
                ),
            )
        ).scalar_one_or_none()

        if admin_unit is None:
            return None

        def color(value):
            return str(value) if value else None

        return OrganizationSettingsReadModel(
            id=admin_unit.id,
            name=admin_unit.name,
            short_name=admin_unit.short_name,
            description=admin_unit.description,
            url=admin_unit.url,
            email=admin_unit.email,
            phone=admin_unit.phone,
            fax=admin_unit.fax,
            location=to_location_read_model(admin_unit.location),
            logo=to_image_edit_read_model(admin_unit.logo),
            can_verify_other=bool(admin_unit.can_verify_other),
            incoming_verification_requests_allowed=bool(
                admin_unit.incoming_verification_requests_allowed
            ),
            incoming_verification_requests_text=(
                admin_unit.incoming_verification_requests_text
            ),
            incoming_verification_requests_postal_codes=list(
                admin_unit.incoming_verification_requests_postal_codes or []
            ),
            widget_font=admin_unit.widget_font,
            widget_background_color=color(admin_unit.widget_background_color),
            widget_primary_color=color(admin_unit.widget_primary_color),
            widget_link_color=color(admin_unit.widget_link_color),
            deletion_requested_at=admin_unit.deletion_requested_at,
        )

    def get_api_key_by_hash(self, key_hash: str) -> Optional[ApiKeyReadModel]:
        row = self.session.execute(
            select(
                ApiKey.id,
                ApiKey.name,
                ApiKey.admin_unit_id,
                ApiKey.user_id,
                ApiKey.rate_limit_value,
            )
            .where(ApiKey.key_hash == key_hash)
            .limit(1)
        ).one_or_none()

        if row is None:
            return None

        return ApiKeyReadModel(
            id=row.id,
            name=row.name,
            admin_unit_id=row.admin_unit_id,
            user_id=row.user_id,
            rate_limit_value=row.rate_limit_value,
        )

    def count_incoming_badges(
        self, admin_unit_id: ObjectId
    ) -> ManageMenuOptionsReadModel:
        reference_requests = self.session.execute(
            select(func.count())
            .select_from(EventReferenceRequest)
            .where(
                EventReferenceRequest.admin_unit_id == admin_unit_id,
                EventReferenceRequest.review_status
                == EventReferenceRequestReviewStatus.inbox,
            )
        ).scalar_one()
        verification_requests = self.session.execute(
            select(func.count())
            .select_from(AdminUnitVerificationRequest)
            .where(
                AdminUnitVerificationRequest.target_admin_unit_id == admin_unit_id,
                AdminUnitVerificationRequest.review_status
                == AdminUnitVerificationRequestReviewStatus.inbox,
            )
        ).scalar_one()

        return ManageMenuOptionsReadModel(
            reference_requests_incoming_badge=reference_requests,
            verification_requests_incoming_badge=verification_requests,
        )

    def member_grants(
        self, admin_unit_id: ObjectId, user_id: ObjectId
    ) -> MemberGrantsReadModel:
        # `permissions` is an AsaList column, so the roles are flattened in Python.
        roles = (
            self.session.execute(
                select(AdminUnitMemberRole)
                .join(AdminUnitMemberRole.members)
                .where(
                    AdminUnitMember.admin_unit_id == admin_unit_id,
                    AdminUnitMember.user_id == user_id,
                )
                .order_by(AdminUnitMemberRole.id)
            )
            .scalars()
            .all()
        )

        return MemberGrantsReadModel(
            roles=[role.name for role in roles],
            permissions=[
                permission for role in roles for permission in role.permissions or []
            ],
        )

    def event_report_recipients(
        self, admin_unit_id: ObjectId, permission: str
    ) -> List[MailRecipientReadModel]:
        members = (
            self.session.execute(
                select(AdminUnitMember)
                .options(selectinload(AdminUnitMember.roles))
                .where(AdminUnitMember.admin_unit_id == admin_unit_id)
            )
            .scalars()
            .all()
        )
        member_user_ids = {
            member.user_id
            for member in members
            if any(permission in role.get_permissions() for role in member.roles)
        }

        rows = self.session.execute(
            select(User.id, User.email, User.locale)
            .where(
                or_(
                    User.id.in_(member_user_ids),
                    User.roles.any(Role.name == "admin"),
                )
            )
            .order_by(User.id)
        ).all()

        return [
            MailRecipientReadModel(id=row.id, email=row.email, locale=row.locale)
            for row in rows
        ]


_OWNER_COLUMNS = {
    ResourceKind.event: (Event, Event.admin_unit_id),
    ResourceKind.event_place: (EventPlace, EventPlace.admin_unit_id),
    ResourceKind.event_organizer: (EventOrganizer, EventOrganizer.admin_unit_id),
    ResourceKind.custom_widget: (CustomWidget, CustomWidget.admin_unit_id),
    ResourceKind.event_reference: (EventReference, EventReference.admin_unit_id),
    ResourceKind.event_reference_request_target: (
        EventReferenceRequest,
        EventReferenceRequest.admin_unit_id,
    ),
    ResourceKind.organization_relation: (
        AdminUnitRelation,
        AdminUnitRelation.source_admin_unit_id,
    ),
    ResourceKind.organization_invitation: (
        AdminUnitInvitation,
        AdminUnitInvitation.admin_unit_id,
    ),
    ResourceKind.verification_request_source: (
        AdminUnitVerificationRequest,
        AdminUnitVerificationRequest.source_admin_unit_id,
    ),
    ResourceKind.verification_request_target: (
        AdminUnitVerificationRequest,
        AdminUnitVerificationRequest.target_admin_unit_id,
    ),
}


def _to_organization(row) -> CurrentOrganizationReadModel:
    return CurrentOrganizationReadModel(
        id=row.id,
        name=row.name,
        short_name=row.short_name,
        is_verified=bool(row.is_verified),
        can_verify_other=bool(row.can_verify_other),
        can_invite_other=bool(row.can_invite_other),
        can_create_other=bool(row.can_create_other),
        incoming_reference_requests_allowed=bool(
            row.incoming_reference_requests_allowed
        ),
        incoming_verification_requests_allowed=bool(
            row.incoming_verification_requests_allowed
        ),
        location=(
            LocationReadModel(
                street=row.street,
                postalCode=row.postalCode,
                city=row.city,
                state=row.state,
                country=row.country,
                latitude=row.latitude,
                longitude=row.longitude,
            )
            if row.location_id is not None
            else None
        ),
    )
