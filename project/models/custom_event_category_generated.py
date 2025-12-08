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


class CustomEventCategoryGeneratedMixin:
    __tablename__ = "customeventcategory"
    __table_args__ = (UniqueConstraint("name", "category_set_id"),)

    __model_name__ = "custom_event_category"
    __model_name_plural__ = "custom_event_categories"
    __display_name__ = "Custom event category"
    __display_name_plural__ = "Custom event categories"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def label(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def category_set_id(cls):
        return Column(
            Integer(),
            ForeignKey("customeventcategoryset.id", ondelete="CASCADE"),
            nullable=False,
        )

    @declared_attr
    def category_set(cls):
        return relationship(
            "CustomEventCategorySet",
            foreign_keys=[cls.category_set_id],
            back_populates="categories",
        )

    @declared_attr
    def events(cls):
        return relationship(
            "Event",
            back_populates="custom_categories",
            secondary="event_customeventcategories",
        )
