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


class LicenseGeneratedMixin(TrackableMixin):
    __tablename__ = "license"

    __model_name__ = "license"
    __model_name_plural__ = "licenses"
    __display_name__ = "License"
    __display_name_plural__ = "Licenses"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def sort(cls):
        return Column(Integer(), nullable=False, default=0, server_default="0")

    @declared_attr
    def code(cls):
        return Column(Unicode(255), unique=True, nullable=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), unique=True, nullable=True)

    @declared_attr
    def url(cls):
        return Column(Unicode(255), unique=True, nullable=True)

    @declared_attr
    def images(cls):
        return relationship(
            "Image",
            back_populates="license",
            primaryjoin="Image.license_id == License.id",
        )
