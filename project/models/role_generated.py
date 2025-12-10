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


class RoleGeneratedMixin:
    __tablename__ = "role"

    __model_name__ = "role"
    __model_name_plural__ = "roles"
    __display_name__ = "Role"
    __display_name_plural__ = "Roles"

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
    def users(cls):
        return relationship(
            "User",
            back_populates="roles",
            secondary="roles_users",
        )
