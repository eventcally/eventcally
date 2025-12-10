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


class ImageGeneratedMixin(TrackableMixin):
    __tablename__ = "image"

    __model_name__ = "image"
    __model_name_plural__ = "images"
    __display_name__ = "Image"
    __display_name_plural__ = "Images"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def data(cls):
        return deferred(Column(LargeBinary, nullable=True))

    @declared_attr
    def encoding_format(cls):
        return Column(Unicode(80), nullable=True)

    @declared_attr
    def copyright_text(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def license_id(cls):
        return Column(
            Integer(), ForeignKey("license.id", ondelete="SET NULL"), nullable=True
        )

    @declared_attr
    def license(cls):
        return relationship(
            "License",
            foreign_keys=[cls.license_id],
            back_populates="images",
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            uselist=False,
            back_populates="logo",
        )

    @declared_attr
    def event(cls):
        return relationship(
            "Event",
            uselist=False,
            back_populates="photo",
        )

    @declared_attr
    def event_organizer(cls):
        return relationship(
            "EventOrganizer",
            uselist=False,
            back_populates="logo",
        )

    @declared_attr
    def event_place(cls):
        return relationship(
            "EventPlace",
            uselist=False,
            back_populates="photo",
        )
