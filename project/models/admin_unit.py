from flask_security import RoleMixin
from sqlalchemy import Column, ForeignKey, Integer, and_, func, select
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased

from project import db
from project.models.admin_unit_generated import AdminUnitGeneratedMixin
from project.models.admin_unit_invitation_generated import (
    AdminUnitInvitationGeneratedMixin,
)
from project.models.admin_unit_member_generated import AdminUnitMemberGeneratedMixin
from project.models.admin_unit_member_invitation_generated import (
    AdminUnitMemberInvitationGeneratedMixin,
)
from project.models.admin_unit_member_role_generated import (
    AdminUnitMemberRoleGeneratedMixin,
)
from project.models.admin_unit_relation_generated import AdminUnitRelationGeneratedMixin
from project.models.api_key_owner_mixin import ApiKeyOwnerMixin
from project.utils import make_check_violation


class AdminUnitMemberRolesMembers(db.Model):
    __tablename__ = "adminunitmemberroles_members"
    __display_name__ = "Organization member role members"
    id = Column(Integer(), primary_key=True)
    member_id = Column("member_id", Integer(), ForeignKey("adminunitmember.id"))
    role_id = Column("role_id", Integer(), ForeignKey("adminunitmemberrole.id"))


class AdminUnitMemberRole(db.Model, AdminUnitMemberRoleGeneratedMixin, RoleMixin):
    pass


class AdminUnitMember(db.Model, AdminUnitMemberGeneratedMixin):
    def __str__(self):
        return self.user.__str__() if self.user else super().__str__()

    def has_role(self, role: str | RoleMixin) -> bool:
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        if isinstance(role, str):
            return role in (role.name for role in self.roles)
        else:  # pragma: no cover
            return role in self.roles

    @hybrid_property
    def is_admin(self):
        return self.has_role("admin")

    @is_admin.expression
    def is_admin(cls):
        return (
            select(func.count())
            .select_from(AdminUnitMemberRole.__table__)
            .join(
                AdminUnitMemberRolesMembers.__table__,
                AdminUnitMemberRolesMembers.role_id == AdminUnitMemberRole.id,
            )
            .where(
                and_(
                    AdminUnitMemberRolesMembers.member_id == cls.id,
                    AdminUnitMemberRole.name == "admin",
                )
            )
            .scalar_subquery()
        ) > 0


class AdminUnitMemberInvitation(db.Model, AdminUnitMemberInvitationGeneratedMixin):
    pass


class AdminUnitInvitation(db.Model, AdminUnitInvitationGeneratedMixin):
    pass


class AdminUnitRelation(db.Model, AdminUnitRelationGeneratedMixin):
    def validate(self):
        source_id = (
            self.source_admin_unit.id
            if self.source_admin_unit
            else self.source_admin_unit_id
        )
        target_id = (
            self.target_admin_unit.id
            if self.target_admin_unit
            else self.target_admin_unit_id
        )
        if source_id == target_id:
            raise make_check_violation("There must be no self-reference.")


@listens_for(AdminUnitRelation, "before_insert")
@listens_for(AdminUnitRelation, "before_update")
def before_saving_admin_unit_relation(mapper, connect, self):
    self.validate()


class AdminUnit(db.Model, AdminUnitGeneratedMixin, ApiKeyOwnerMixin):
    def get_number_of_api_keys(self):
        from project.models.api_key import ApiKey

        return ApiKey.query.filter(ApiKey.admin_unit_id == self.id).count()

    @hybrid_property
    def is_verified(self):
        if not self.incoming_relations:
            return False

        return any(
            r.verify and r.source_admin_unit.can_verify_other
            for r in self.incoming_relations
        )

    @is_verified.expression
    def is_verified(cls):
        SourceAdminUnit = aliased(AdminUnit)

        j = AdminUnitRelation.__table__.join(
            SourceAdminUnit,
            AdminUnitRelation.source_admin_unit_id == SourceAdminUnit.id,
        )
        return (
            select(func.count())
            .select_from(j)
            .where(
                and_(
                    AdminUnitRelation.verify,
                    AdminUnitRelation.target_admin_unit_id == cls.id,
                    SourceAdminUnit.can_verify_other,
                )
            )
            .scalar_subquery()
            > 0
        )

    def __str__(self):
        return self.name or super().__str__()


@listens_for(AdminUnit.can_invite_other, "set")
def set_admin_unit_can_invite_other(target, value, oldvalue, initiator):
    if (
        not value
        and target.admin_unit_invitations
        and len(target.admin_unit_invitations) > 0
    ):
        target.admin_unit_invitations = []
