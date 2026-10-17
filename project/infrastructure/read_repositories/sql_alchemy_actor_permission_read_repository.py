from typing import Optional

from sqlalchemy import exists, func, select

from project.application.read_repositories.abstract_actor_permission_read_repository import (
    AbstractActorPermissionReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.models import (
    AdminUnit,
    AdminUnitMember,
    AdminUnitMemberRole,
    AppInstallation,
    Role,
    User,
)


class SqlAlchemyActorPermissionReadRepository(AbstractActorPermissionReadRepository):
    """Answers on the injected (read) session; never uses `Model.query`, which is
    bound to the write session."""

    def __init__(self, session):
        super().__init__()
        self.session = session

    def is_platform_admin(self, user_id: ObjectId) -> bool:
        stmt = select(
            exists()
            .where(User.id == user_id)
            .where(User.roles.any(Role.name == "admin"))
        )
        return self.session.execute(stmt).scalar_one()

    def member_has_permission(
        self, admin_unit_id: ObjectId, user_id: ObjectId, permission: str
    ) -> bool:
        # `permissions` is an AsaList column, so it cannot be filtered in SQL.
        stmt = (
            select(AdminUnitMemberRole)
            .join(AdminUnitMemberRole.members)
            .where(
                AdminUnitMember.admin_unit_id == admin_unit_id,
                AdminUnitMember.user_id == user_id,
            )
        )
        roles = self.session.execute(stmt).scalars().all()
        return any(permission in role.get_permissions() for role in roles)

    def installation_has_permission(
        self, app_installation_id: ObjectId, admin_unit_id: ObjectId, permission: str
    ) -> bool:
        row = self.session.execute(
            select(AppInstallation.admin_unit_id, AppInstallation.permissions).where(
                AppInstallation.id == app_installation_id
            )
        ).one_or_none()

        if row is None:
            return False

        return row.admin_unit_id == admin_unit_id and permission in (
            row.permissions or []
        )

    def user_email(self, user_id: ObjectId) -> Optional[str]:
        return self.session.execute(
            select(User.email).where(User.id == user_id)
        ).scalar_one_or_none()

    def is_member_of_verified_organization(self, user_id: ObjectId) -> bool:
        return (
            self.session.execute(
                select(func.count())
                .select_from(AdminUnitMember)
                .join(AdminUnit, AdminUnit.id == AdminUnitMember.admin_unit_id)
                .where(AdminUnitMember.user_id == user_id, AdminUnit.is_verified)
            ).scalar_one()
            > 0
        )

    def installation_organization_is_verified(
        self, app_installation_id: ObjectId
    ) -> bool:
        return (
            self.session.execute(
                select(func.count())
                .select_from(AppInstallation)
                .join(AdminUnit, AdminUnit.id == AppInstallation.admin_unit_id)
                .where(AppInstallation.id == app_installation_id, AdminUnit.is_verified)
            ).scalar_one()
            > 0
        )
