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


class EventListGeneratedMixin(TrackableMixin):
    __tablename__ = "eventlist"
    __table_args__ = (UniqueConstraint("name", "admin_unit_id"),)

    __model_name__ = "event_list"
    __model_name_plural__ = "event_lists"
    __display_name__ = "Event list"
    __display_name_plural__ = "Event lists"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=True)

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
            back_populates="event_lists",
        )

    @declared_attr
    def events(cls):
        return relationship(
            "Event",
            back_populates="event_lists",
            secondary="event_eventlists",
        )
