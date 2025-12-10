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
from project.models.trackable_mixin import TrackableMixin
from project.models.rate_limit_holder_mixin import RateLimitHolderMixin


class OAuth2ClientGeneratedMixin(TrackableMixin, RateLimitHolderMixin):
    __tablename__ = "oauth2_client"
    __table_args__ = (
        CheckConstraint(
            "(admin_unit_id IS NULL) <> (user_id IS NULL)",
            name="oauth2_client_admin_unit_xor_user",
        ),
    )

    __model_name__ = "oauth2_client"
    __model_name_plural__ = "oauth2_clients"
    __display_name__ = "OAuth2 client"
    __display_name_plural__ = "OAuth2 clients"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def homepage_url(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def setup_url(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def webhook_url(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def webhook_secret(cls):
        return deferred(Column(Unicode(255), nullable=True), group="detail")

    @declared_attr
    def description(cls):
        return deferred(Column(UnicodeText(), nullable=True), group="detail")

    @declared_attr
    def app_permissions(cls):
        return Column(MutableList.as_mutable(AsaList()), nullable=True)

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=True
        )

    @declared_attr
    def user_id(cls):
        return Column(
            Integer(), ForeignKey("user.id", ondelete="CASCADE"), nullable=True
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="oauth2_clients",
        )

    @declared_attr
    def user(cls):
        return relationship(
            "User",
            foreign_keys=[cls.user_id],
            back_populates="oauth2_clients",
        )

    @declared_attr
    def app_installations(cls):
        return relationship(
            "AppInstallation",
            cascade="all, delete-orphan",
            back_populates="oauth2_client",
            primaryjoin="AppInstallation.oauth2_client_id == OAuth2Client.id",
        )

    @declared_attr
    def app_keys(cls):
        return relationship(
            "AppKey",
            cascade="all, delete-orphan",
            back_populates="oauth2_client",
            primaryjoin="AppKey.oauth2_client_id == OAuth2Client.id",
        )

    @declared_attr
    def app_oauth2_tokens(cls):
        return relationship(
            "OAuth2Token",
            cascade="all, delete-orphan",
            back_populates="app",
            primaryjoin="OAuth2Token.app_id == OAuth2Client.id",
        )
