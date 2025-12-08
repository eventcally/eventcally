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


class AdminUnitMemberRoleGeneratedMixin:
    __tablename__ = "adminunitmemberrole"

    __model_name__ = "admin_unit_member_role"
    __model_name_plural__ = "admin_unit_member_roles"
    __display_name__ = "Organization member role"
    __display_name_plural__ = "Organization member roles"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(80), unique=True, nullable=True)

    @declared_attr
    def title(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def description(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def permissions(cls):
        return Column(MutableList.as_mutable(AsaList()), nullable=True)

    @declared_attr
    def members(cls):
        return relationship(
            "AdminUnitMember",
            back_populates="roles",
            secondary="adminunitmemberroles_members",
        )
