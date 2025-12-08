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


class EventDateGeneratedMixin:
    __tablename__ = "eventdate"

    __model_name__ = "event_date"
    __model_name_plural__ = "event_dates"
    __display_name__ = "Event date"
    __display_name_plural__ = "Event dates"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def start(cls):
        return Column(DateTime(timezone=True), nullable=False, index=True)

    @declared_attr
    def end(cls):
        return Column(DateTime(timezone=True), index=True, nullable=True)

    @declared_attr
    def allday(cls):
        return Column(Boolean(), nullable=False, default=False, server_default="0")

    @declared_attr
    def event_id(cls):
        return Column(
            Integer(), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def event(cls):
        return relationship(
            "Event",
            foreign_keys=[cls.event_id],
            back_populates="dates",
        )
