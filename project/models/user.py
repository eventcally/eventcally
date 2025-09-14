import datetime

from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_security import AsaList, RoleMixin, UserMixin
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UniqueConstraint,
)
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import backref, deferred, relationship

from project import db
from project.models.api_key import ApiKeyOwnerMixin


class RolesUsers(db.Model):
    __tablename__ = "roles_users"
    id = Column(Integer(), primary_key=True)
    user_id = Column("user_id", Integer(), ForeignKey("user.id"))
    role_id = Column("role_id", Integer(), ForeignKey("role.id"))


class Role(db.Model, RoleMixin):
    __tablename__ = "role"
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    title = Column(Unicode(255))
    description = Column(String(255))
    permissions = Column(MutableList.as_mutable(AsaList()), nullable=True)

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class User(db.Model, UserMixin, ApiKeyOwnerMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    active = Column(Boolean())
    fs_uniquifier = Column(String(255))
    confirmed_at = Column(DateTime())
    roles = relationship(
        "Role", secondary="roles_users", backref=backref("users", lazy="dynamic")
    )
    favorite_events = relationship(
        "Event",
        secondary="user_favoriteevents",
        backref=backref("favored_by_users", lazy=True),
    )
    newsletter_enabled = deferred(
        Column(
            Boolean(),
            nullable=True,
            default=True,
            server_default="1",
        )
    )
    tos_accepted_at = Column(
        DateTime(),
        nullable=True,
    )
    created_at = deferred(Column(DateTime, default=datetime.datetime.utcnow))
    deletion_requested_at = deferred(Column(DateTime, nullable=True))
    locale = Column(String(255), nullable=True)
    api_keys = relationship(
        "ApiKey",
        primaryjoin="ApiKey.user_id == User.id",
        cascade="all, delete-orphan",
        backref=backref("user", lazy=True),
    )
    oauth2_clients = relationship(
        "OAuth2Client",
        primaryjoin="OAuth2Client.user_id == User.id",
        cascade="all, delete-orphan",
        backref=backref("user", lazy=True),
    )

    def get_number_of_api_keys(self):
        from project.models.api_key import ApiKey

        return ApiKey.query.filter(ApiKey.user_id == self.id).count()

    @property
    def is_member_of_verified_admin_unit(self):
        if not self.adminunitmembers:  # pragma: no cover
            return False

        return any(
            m.adminunit and m.adminunit.is_verified for m in self.adminunitmembers
        )

    def __str__(self):
        return self.email or super().__str__()


class UserFavoriteEvents(db.Model):
    __tablename__ = "user_favoriteevents"
    __table_args__ = (UniqueConstraint("user_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)


# OAuth Consumer: Wenn wir OAuth consumen und sich ein Nutzer per Google oder Facebook anmelden möchte


class OAuth(OAuthConsumerMixin, db.Model):
    __display_name__ = "OAuth connection"
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
