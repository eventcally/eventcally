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


class AdminUnitMemberGeneratedMixin:
    __tablename__ = "adminunitmember"

    __model_name__ = "organization_member"
    __model_name_plural__ = "organization_members"
    __display_name__ = "Organization member"
    __display_name_plural__ = "Organization members"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def user_id(cls):
        return Column(
            Integer(), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="members",
        )

    @declared_attr
    def user(cls):
        return relationship(
            "User",
            foreign_keys=[cls.user_id],
            back_populates="admin_unit_memberships",
        )

    @declared_attr
    def roles(cls):
        return relationship(
            "AdminUnitMemberRole",
            back_populates="members",
            secondary="adminunitmemberroles_members",
            order_by="AdminUnitMemberRole.id",
        )
