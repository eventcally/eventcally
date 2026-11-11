from enum import IntEnum
from flask_security import AsaList
from geoalchemy2 import Geometry
from project.infrastructure.extensions import db
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
from project.infrastructure.dbtypes import IntegerEnum
from sqlalchemy.ext.declarative import declared_attr
from project.infrastructure.models.mixins.trackable_mixin import TrackableMixin


class CalendarGeneratedMixin(TrackableMixin):
    __tablename__ = "calendar"
    __table_args__ = (UniqueConstraint("admin_unit_id", "name"),)

    __model_name__ = "calendar"
    __model_name_plural__ = "calendars"
    __display_name__ = "Calendar"
    __display_name_plural__ = "Calendars"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def description(cls):
        return Column(UnicodeText(), nullable=True)

    @declared_attr
    def private(cls):
        return Column(Boolean(), nullable=False, default=False, server_default="0")

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="calendars",
        )

    @declared_attr
    def entries(cls):
        return relationship(
            "CalendarEntry",
            cascade="all, delete-orphan",
            back_populates="calendar",
            primaryjoin="CalendarEntry.calendar_id == Calendar.id",
        )
