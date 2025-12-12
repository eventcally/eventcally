from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_security import RoleMixin, UserMixin
from sqlalchemy import Column, ForeignKey, Integer, String

from project import db
from project.models.association_tables.roles_users_generated import (
    RolesUsersGeneratedMixin,
)
from project.models.association_tables.user_favorite_event_generated import (
    UserFavoriteEventGeneratedMixin,
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
    def get_number_of_api_keys(self):
        from project.models.api_key import ApiKey

        return ApiKey.query.filter(ApiKey.user_id == self.id).count()

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


class UserFavoriteEvents(db.Model, UserFavoriteEventGeneratedMixin):
    pass


# OAuth Consumer: Wenn wir OAuth consumen und sich ein Nutzer per Google oder Facebook anmelden möchte


class OAuth(OAuthConsumerMixin, db.Model):
    __display_name__ = "OAuth connection"
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
