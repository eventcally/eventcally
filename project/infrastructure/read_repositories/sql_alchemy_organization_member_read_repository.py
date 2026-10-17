from typing import List, Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from project.application.queries.list_organization_members_query import (
    ListOrganizationMembersQuery,
)
from project.application.queries.list_user_organization_memberships_query import (
    ListUserOrganizationMembershipsQuery,
)
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberReadModel,
    OrganizationMemberRoleReadModel,
    UserOrganizationMembershipReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_models.user_ref_read_model import UserRefReadModel
from project.application.read_repositories.abstract_organization_member_read_repository import (
    AbstractOrganizationMemberReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    AdminUnitMember,
    AdminUnitMemberRole,
    User,
)
from project.infrastructure.read_repositories.query_helpers import paginate


class SqlAlchemyOrganizationMemberReadRepository(
    AbstractOrganizationMemberReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: ListOrganizationMembersQuery
    ) -> Page[OrganizationMemberReadModel]:
        filters = [AdminUnitMember.admin_unit_id == query.admin_unit_id]
        stmt = (
            select(AdminUnitMember)
            .join(AdminUnitMember.user)
            .where(*filters)
            .options(
                contains_eager(AdminUnitMember.user).load_only(User.id, User.email),
                selectinload(AdminUnitMember.roles),
            )
            .order_by(func.lower(User.email), AdminUnitMember.id)
        )
        count_stmt = select(AdminUnitMember.id).where(*filters)

        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_member(row[0])
        )

    def get(self, object_id: ObjectId) -> Optional[OrganizationMemberReadModel]:
        stmt = (
            select(AdminUnitMember)
            .where(AdminUnitMember.id == object_id)
            .options(
                joinedload(AdminUnitMember.user).load_only(User.id, User.email),
                selectinload(AdminUnitMember.roles),
            )
        )
        member = self.session.execute(stmt).scalar_one_or_none()
        return _to_member(member) if member else None

    def list_for_user(
        self, query: ListUserOrganizationMembershipsQuery
    ) -> Page[UserOrganizationMembershipReadModel]:
        filters = [AdminUnitMember.user_id == query.user_id]
        stmt = _membership_select().where(*filters).order_by(AdminUnitMember.id)
        count_stmt = select(AdminUnitMember.id).where(*filters)

        return paginate(self.session, stmt, count_stmt, query.page, _to_membership)

    def get_membership(
        self, object_id: ObjectId
    ) -> Optional[UserOrganizationMembershipReadModel]:
        row = self.session.execute(
            _membership_select().where(AdminUnitMember.id == object_id)
        ).one_or_none()
        return _to_membership(row) if row else None

    def list_roles(self) -> List[OrganizationMemberRoleReadModel]:
        roles = self.session.execute(
            select(AdminUnitMemberRole).order_by(AdminUnitMemberRole.id)
        ).scalars()
        return [_to_role(role) for role in roles]


def _to_role(role) -> OrganizationMemberRoleReadModel:
    return OrganizationMemberRoleReadModel(id=role.id, name=role.name, title=role.title)


def _to_member(member) -> OrganizationMemberReadModel:
    return OrganizationMemberReadModel(
        id=member.id,
        admin_unit_id=member.admin_unit_id,
        user_id=member.user_id,
        user=UserRefReadModel(id=member.user.id, email=member.user.email),
        roles=[_to_role(role) for role in sorted(member.roles, key=lambda r: r.id)],
    )


def _membership_select():
    return select(AdminUnitMember, AdminUnitMember.is_admin).options(
        joinedload(AdminUnitMember.admin_unit).load_only(AdminUnit.id, AdminUnit.name)
    )


def _to_membership(row) -> UserOrganizationMembershipReadModel:
    """`row` is (member, is_admin) of `_membership_select`."""
    member, is_admin = row

    return UserOrganizationMembershipReadModel(
        id=member.id,
        admin_unit_id=member.admin_unit_id,
        user_id=member.user_id,
        is_admin=bool(is_admin),
        admin_unit=OrganizationRefReadModel(
            id=member.admin_unit.id, name=member.admin_unit.name
        ),
    )
