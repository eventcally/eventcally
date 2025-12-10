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
from project.models.api_key_owner_mixin import ApiKeyOwnerMixin
from project.models.rate_limit_holder_mixin import RateLimitHolderMixin


class ApiKeyGeneratedMixin(TrackableMixin, ApiKeyOwnerMixin, RateLimitHolderMixin):
    __tablename__ = "apikey"
    __table_args__ = (
        CheckConstraint(
            "(admin_unit_id IS NULL) <> (user_id IS NULL)",
            name="apikey_admin_unit_xor_user",
        ),
        UniqueConstraint("name", "admin_unit_id", name="uq_apikey_name_admin_unit_id"),
        UniqueConstraint("name", "user_id", name="uq_apikey_name_user_id"),
    )

    __model_name__ = "api_key"
    __model_name_plural__ = "api_keys"
    __display_name__ = "API key"
    __display_name_plural__ = "API keys"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def key_hash(cls):
        return Column(Unicode(255), nullable=False, unique=True)

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
            back_populates="api_keys",
        )

    @declared_attr
    def user(cls):
        return relationship(
            "User",
            foreign_keys=[cls.user_id],
            back_populates="api_keys",
        )
