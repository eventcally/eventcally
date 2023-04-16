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


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def get_user_id(self):
        return self.id


class UserFavoriteEvents(db.Model):
    __tablename__ = "user_favoriteevents"
    __table_args__ = (UniqueConstraint("user_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)


# OAuth Consumer: Wenn wir OAuth consumen und sich ein Nutzer per Google oder Facebook anmelden möchte


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = Column(String(256), unique=True, nullable=False)
    user_id = Column(Integer(), ForeignKey("user.id"), nullable=False)
    user = db.relationship("User")
