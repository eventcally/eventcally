from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload

from project.application.queries.list_organization_member_invitations_query import (
    ListOrganizationMemberInvitationsQuery,
)
from project.application.queries.list_user_member_invitations_query import (
    ListUserMemberInvitationsQuery,
)
from project.application.read_models.organization_member_invitation_read_models import (
    OrganizationMemberInvitationReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_member_invitation_read_repository import (
    AbstractOrganizationMemberInvitationReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, AdminUnitMemberInvitation, User
from project.infrastructure.read_repositories.query_helpers import paginate

_load_admin_unit = joinedload(AdminUnitMemberInvitation.admin_unit).load_only(
    AdminUnit.id, AdminUnit.name
)


class SqlAlchemyOrganizationMemberInvitationReadRepository(
    AbstractOrganizationMemberInvitationReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: ListOrganizationMemberInvitationsQuery
    ) -> Page[OrganizationMemberInvitationReadModel]:
        filters = [AdminUnitMemberInvitation.admin_unit_id == query.admin_unit_id]
        stmt = (
            select(AdminUnitMemberInvitation)
            .where(*filters)
            .options(_load_admin_unit)
            .order_by(
                func.lower(AdminUnitMemberInvitation.email),
                AdminUnitMemberInvitation.id,
            )
        )
        count_stmt = select(AdminUnitMemberInvitation.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )

    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationMemberInvitationReadModel]:
        invitation = self.session.execute(
            select(AdminUnitMemberInvitation)
            .where(AdminUnitMemberInvitation.id == object_id)
            .options(_load_admin_unit)
        ).scalar_one_or_none()
        return _to_model(invitation) if invitation else None

    def list_for_user(
        self, query: ListUserMemberInvitationsQuery
    ) -> Page[OrganizationMemberInvitationReadModel]:
        user_email = (
            select(User.email).where(User.id == query.user_id).scalar_subquery()
        )
        filters = [
            func.lower(AdminUnitMemberInvitation.email) == func.lower(user_email)
        ]
        stmt = (
            select(AdminUnitMemberInvitation)
            .where(*filters)
            .options(_load_admin_unit)
            .order_by(AdminUnitMemberInvitation.id)
        )
        count_stmt = select(AdminUnitMemberInvitation.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )

    def get_recipient_email(self, object_id: ObjectId) -> Optional[str]:
        return self.session.execute(
            select(AdminUnitMemberInvitation.email).where(
                AdminUnitMemberInvitation.id == object_id
            )
        ).scalar_one_or_none()


def _to_model(invitation) -> OrganizationMemberInvitationReadModel:
    return OrganizationMemberInvitationReadModel(
        id=invitation.id,
        admin_unit_id=invitation.admin_unit_id,
        email=invitation.email,
        roles=invitation.roles,
        admin_unit=OrganizationRefReadModel(
            id=invitation.admin_unit.id, name=invitation.admin_unit.name
        ),
    )
