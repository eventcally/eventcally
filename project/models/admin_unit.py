from __future__ import annotations

from typing import Optional

from flask_security import RoleMixin
from sqlalchemy import and_, func, select
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import aliased

from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)
from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.extensions import db
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
from project.models.association_tables.admin_unit_member_roles_members_generated import (
    AdminUnitMemberRolesMembersGeneratedMixin,
)
from project.models.mixins.api_key_owner_mixin import ApiKeyOwnerMixin
from project.utils import make_check_violation


class AdminUnitMemberRolesMembers(db.Model, AdminUnitMemberRolesMembersGeneratedMixin):
    pass


class AdminUnitMemberRole(db.Model, AdminUnitMemberRoleGeneratedMixin, RoleMixin):
    pass


class AdminUnitMember(db.Model, AdminUnitMemberGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: OrganisationMemberAggregate) -> AdminUnitMember:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: OrganisationMemberAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.user_id = aggregate.user_id
        self.roles = AdminUnitMemberRole.query.filter(
            AdminUnitMemberRole.name.in_(aggregate.roles)
        ).all()

    @classmethod
    def to_aggregate(cls, model: AdminUnitMember) -> OrganisationMemberAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = OrganisationMemberAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            user_id=model.user_id,
            roles=[role.name for role in model.roles],
        )

        return aggregate

    def __str__(self):
        return self.user.__str__() if self.user else super().__str__()

    def has_role(self, role: str | RoleMixin) -> bool:
        """Returns `True` if the user identifies with the specified role.

        :param role: A role name or `Role` instance"""
        if isinstance(role, str):
            return role in (role.name for role in self.roles)
        else:  # pragma: no cover
            return role in self.roles

    def has_permission(self, permission: str) -> bool:
        """Returns `True` if the user has the specified permission through any of their roles.

        :param permission: The name of the permission to check for."""
        for role in self.roles:
            if permission in role.get_permissions():
                return True
        return False  # pragma: no cover

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
    @classmethod
    def from_aggregate(
        cls, aggregate: AdminUnitMemberInvitationAggregate
    ) -> AdminUnitMemberInvitation:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: AdminUnitMemberInvitationAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.email = aggregate.email
        self.roles = ",".join(aggregate.roles) if aggregate.roles else None

    @classmethod
    def to_aggregate(
        cls, model: Optional[AdminUnitMemberInvitation]
    ) -> Optional[AdminUnitMemberInvitationAggregate]:
        if model is None:  # pragma: no cover
            return None

        return AdminUnitMemberInvitationAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            email=model.email,
            roles=model.roles.split(",") if model.roles else [],
        )


class AdminUnitInvitation(db.Model, AdminUnitInvitationGeneratedMixin):
    @classmethod
    def from_aggregate(
        cls, aggregate: AdminUnitInvitationAggregate
    ) -> AdminUnitInvitation:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: AdminUnitInvitationAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.email = aggregate.email
        self.admin_unit_name = aggregate.admin_unit_name
        self.relation_auto_verify_event_reference_requests = (
            aggregate.relation_auto_verify_event_reference_requests
        )
        self.relation_verify = aggregate.relation_verify

    @classmethod
    def to_aggregate(
        cls, model: Optional[AdminUnitInvitation]
    ) -> Optional[AdminUnitInvitationAggregate]:
        if model is None:  # pragma: no cover
            return None

        return AdminUnitInvitationAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            email=model.email,
            admin_unit_name=model.admin_unit_name,
            relation_auto_verify_event_reference_requests=(
                model.relation_auto_verify_event_reference_requests
            ),
            relation_verify=model.relation_verify,
        )


class AdminUnitRelation(db.Model, AdminUnitRelationGeneratedMixin):
    @classmethod
    def from_aggregate(
        cls, aggregate: OrganizationRelationAggregate
    ) -> AdminUnitRelation:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: OrganizationRelationAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.source_admin_unit_id = aggregate.source_admin_unit_id
        self.target_admin_unit_id = aggregate.target_admin_unit_id
        self.auto_verify_event_reference_requests = (
            aggregate.auto_verify_event_reference_requests
        )
        self.verify = aggregate.verify
        self.invited = aggregate.invited

    @classmethod
    def to_aggregate(
        cls, model: Optional[AdminUnitRelation]
    ) -> Optional[OrganizationRelationAggregate]:
        if model is None:  # pragma: no cover
            return None

        return OrganizationRelationAggregate(
            id=model.id,
            source_admin_unit_id=model.source_admin_unit_id,
            target_admin_unit_id=model.target_admin_unit_id,
            auto_verify_event_reference_requests=model.auto_verify_event_reference_requests,
            verify=model.verify,
            invited=model.invited,
        )

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
    def fill_from_aggregate(self, aggregate: OrganizationAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.deletion_requested_at = aggregate.deletion_requested_at
        self.deletion_requested_by_id = aggregate.deletion_requested_by_id

    @classmethod
    def to_aggregate(
        cls, model: Optional[AdminUnit]
    ) -> Optional[OrganizationAggregate]:
        if model is None:  # pragma: no cover
            return None

        aggregate = OrganizationAggregate(
            id=model.id,
            name=model.name,
            deletion_requested_at=model.deletion_requested_at,
            deletion_requested_by_id=model.deletion_requested_by_id,
            can_verify_other=model.can_verify_other,
            incoming_verification_requests_allowed=model.incoming_verification_requests_allowed,
            incoming_verification_requests_postal_codes=list(
                model.incoming_verification_requests_postal_codes or []
            ),
            location=model.location.to_value_object() if model.location else None,
            max_api_keys=model.max_api_keys,
        )

        return aggregate

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
