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


class EventCategoryGeneratedMixin:
    __tablename__ = "eventcategory"

    __model_name__ = "event_category"
    __model_name_plural__ = "event_categories"
    __display_name__ = "Event category"
    __display_name_plural__ = "Event categories"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=False, unique=True)

    @declared_attr
    def events(cls):
        return relationship(
            "Event",
            back_populates="categories",
            secondary="event_eventcategories",
        )
