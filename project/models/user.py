from __future__ import annotations

from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_security import RoleMixin, UserMixin
from sqlalchemy import Column, ForeignKey, Integer, String

from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.extensions import db
from project.models.association_tables.roles_users_generated import (
    RolesUsersGeneratedMixin,
)
from project.models.mixins.api_key_owner_mixin import ApiKeyOwnerMixin
from project.models.role_generated import RoleGeneratedMixin
from project.models.user_generated import UserGeneratedMixin


class RolesUsers(db.Model, RolesUsersGeneratedMixin):
    pass


class Role(db.Model, RoleGeneratedMixin, RoleMixin):
    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class User(db.Model, UserGeneratedMixin, UserMixin, ApiKeyOwnerMixin):
    def fill_from_aggregate(self, aggregate: UserAggregate):
        self.locale = aggregate.locale
        self.newsletter_enabled = aggregate.newsletter_enabled
        self.deletion_requested_at = aggregate.deletion_requested_at
        self.tos_accepted_at = aggregate.tos_accepted_at
        self.roles = Role.query.filter(Role.name.in_(aggregate.roles)).all()

    @classmethod
    def to_aggregate(cls, model: User) -> UserAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = UserAggregate(
            id=model.id,
            email=model.email,
            locale=model.locale,
            is_platform_admin=any(role.name == "admin" for role in model.roles),
            max_api_keys=model.max_api_keys,
            newsletter_enabled=bool(model.newsletter_enabled),
            deletion_requested_at=model.deletion_requested_at,
            tos_accepted_at=model.tos_accepted_at,
            roles=[r.name for r in model.roles],
        )
        return aggregate

    @property
    def is_member_of_verified_admin_unit(self):
        if not self.admin_unit_memberships:  # pragma: no cover
            return False

        return any(
            m.admin_unit and m.admin_unit.is_verified
            for m in self.admin_unit_memberships
        )

    def __str__(self):
        return self.email or super().__str__()


# OAuth Consumer: Wenn wir OAuth consumen und sich ein Nutzer per Google oder Facebook anmelden möchte


class OAuth(OAuthConsumerMixin, db.Model):
    __display_name__ = "OAuth connection"
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
