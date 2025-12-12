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
from project.models.mixins.trackable_mixin import TrackableMixin


class AppInstallationGeneratedMixin(TrackableMixin):
    __tablename__ = "app_installation"
    __table_args__ = (UniqueConstraint("admin_unit_id", "oauth2_client_id"),)

    __model_name__ = "app_installation"
    __model_name_plural__ = "app_installations"
    __display_name__ = "App installation"
    __display_name_plural__ = "App installations"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def permissions(cls):
        return Column(MutableList.as_mutable(AsaList()), nullable=True)

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def oauth2_client_id(cls):
        return Column(
            Integer(),
            ForeignKey("oauth2_client.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="app_installations",
        )

    @declared_attr
    def oauth2_client(cls):
        return relationship(
            "OAuth2Client",
            foreign_keys=[cls.oauth2_client_id],
            back_populates="app_installations",
        )

    @declared_attr
    def oauth2_tokens(cls):
        return relationship(
            "OAuth2Token",
            cascade="all, delete-orphan",
            back_populates="app_installation",
            primaryjoin="OAuth2Token.app_installation_id == AppInstallation.id",
        )
