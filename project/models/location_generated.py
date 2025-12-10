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


class LocationGeneratedMixin(TrackableMixin):
    __tablename__ = "location"

    __model_name__ = "location"
    __model_name_plural__ = "locations"
    __display_name__ = "Location"
    __display_name_plural__ = "Locations"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def street(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def postalCode(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def city(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def state(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def country(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def latitude(cls):
        return Column(Numeric(18, 16), nullable=True)

    @declared_attr
    def longitude(cls):
        return Column(Numeric(19, 16), nullable=True)

    @declared_attr
    def coordinate(cls):
        return Column(Geometry(geometry_type="POINT"), nullable=True)

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            uselist=False,
            back_populates="location",
        )

    @declared_attr
    def event_organizer(cls):
        return relationship(
            "EventOrganizer",
            uselist=False,
            back_populates="location",
        )

    @declared_attr
    def event_place(cls):
        return relationship(
            "EventPlace",
            uselist=False,
            back_populates="location",
        )
