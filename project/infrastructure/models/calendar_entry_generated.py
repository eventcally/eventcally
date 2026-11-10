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


class CalendarEntryGeneratedMixin(TrackableMixin):
    __tablename__ = "calendarentry"
    __table_args__ = (UniqueConstraint("calendar_id", "event_id"),)

    __model_name__ = "calendar_entry"
    __model_name_plural__ = "calendar_entries"
    __display_name__ = "Calendar entry"
    __display_name_plural__ = "Calendar entries"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def calendar_id(cls):
        return Column(
            Integer(), ForeignKey("calendar.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def event_id(cls):
        return Column(
            Integer(), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def calendar(cls):
        return relationship(
            "Calendar",
            foreign_keys=[cls.calendar_id],
            back_populates="entries",
        )

    @declared_attr
    def event(cls):
        return relationship(
            "Event",
            foreign_keys=[cls.event_id],
            back_populates="calendar_entries",
        )
