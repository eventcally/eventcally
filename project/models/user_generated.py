from enum import IntEnum
from flask_security import AsaList
from geoalchemy2 import Geometry
from project import db
from sqlalchemy import (
    Index,
    Boolean,
    DateTime,
    Column,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Unicode,
    UniqueConstraint,
    ForeignKey,
    UnicodeText,
    CheckConstraint,
    cast,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import backref, deferred, relationship, remote
from sqlalchemy_utils import ColorType
import datetime
from project.dbtypes import IntegerEnum
from sqlalchemy.ext.declarative import declared_attr
from project.models.mixins.api_key_owner_mixin import ApiKeyOwnerMixin


class UserGeneratedMixin(ApiKeyOwnerMixin):
    __tablename__ = "user"

    __model_name__ = "user"
    __model_name_plural__ = "users"
    __display_name__ = "User"
    __display_name_plural__ = "Users"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def email(cls):
        return Column(Unicode(255), unique=True, nullable=True)

    @declared_attr
    def username(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def password(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def active(cls):
        return Column(Boolean(), nullable=True)

    @declared_attr
    def fs_uniquifier(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def confirmed_at(cls):
        return Column(DateTime(), nullable=True)

    @declared_attr
    def newsletter_enabled(cls):
        return deferred(Column(Boolean(), default=True, nullable=True))

    @declared_attr
    def tos_accepted_at(cls):
        return Column(DateTime(), nullable=True)

    @declared_attr
    def created_at(cls):
        return deferred(
            Column(DateTime(), default=datetime.datetime.utcnow, nullable=True)
        )

    @declared_attr
    def deletion_requested_at(cls):
        return deferred(Column(DateTime(), nullable=True))

    @declared_attr
    def locale(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def roles(cls):
        return relationship(
            "Role",
            back_populates="users",
            secondary="roles_users",
        )

    @declared_attr
    def favorite_events(cls):
        return relationship(
            "Event",
            back_populates="favored_by_users",
            secondary="user_favoriteevents",
        )

    @declared_attr
    def api_keys(cls):
        return relationship(
            "ApiKey",
            cascade="all, delete-orphan",
            back_populates="user",
            primaryjoin="ApiKey.user_id == User.id",
        )

    @declared_attr
    def oauth2_clients(cls):
        return relationship(
            "OAuth2Client",
            cascade="all, delete-orphan",
            back_populates="user",
            primaryjoin="OAuth2Client.user_id == User.id",
        )

    @declared_attr
    def oauth2_tokens(cls):
        return relationship(
            "OAuth2Token",
            cascade="all, delete-orphan",
            back_populates="user",
            primaryjoin="OAuth2Token.user_id == User.id",
        )

    @declared_attr
    def admin_unit_memberships(cls):
        return relationship(
            "AdminUnitMember",
            cascade="all, delete-orphan",
            back_populates="user",
            primaryjoin="AdminUnitMember.user_id == User.id",
        )

    @declared_attr
    def admin_units_deletion_requested(cls):
        return relationship(
            "AdminUnit",
            back_populates="deletion_requested_by",
            primaryjoin="AdminUnit.deletion_requested_by_id == User.id",
        )

    @declared_attr
    def oauth2_authorization_codes(cls):
        return relationship(
            "OAuth2AuthorizationCode",
            cascade="all, delete-orphan",
            back_populates="user",
            primaryjoin="OAuth2AuthorizationCode.user_id == User.id",
        )
