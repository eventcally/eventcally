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


class AppKeyGeneratedMixin(TrackableMixin):
    __tablename__ = "app_key"
    __table_args__ = (UniqueConstraint("kid", "oauth2_client_id"),)

    __model_name__ = "app_key"
    __model_name_plural__ = "app_keys"
    __display_name__ = "App key"
    __display_name_plural__ = "App keys"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def checksum(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def kid(cls):
        return Column(Unicode(255), nullable=False, index=True)

    @declared_attr
    def public_key(cls):
        return Column(UnicodeText(), nullable=False)

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
            back_populates="app_keys",
        )

    @declared_attr
    def oauth2_client(cls):
        return relationship(
            "OAuth2Client",
            foreign_keys=[cls.oauth2_client_id],
            back_populates="app_keys",
        )
