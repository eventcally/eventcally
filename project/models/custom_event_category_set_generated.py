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


class CustomEventCategorySetGeneratedMixin:
    __tablename__ = "customeventcategoryset"

    __model_name__ = "custom_event_category_set"
    __model_name_plural__ = "custom_event_category_sets"
    __display_name__ = "Custom event category set"
    __display_name_plural__ = "Custom event category sets"

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
    def categories(cls):
        return relationship(
            "CustomEventCategory",
            cascade="all, delete-orphan",
            back_populates="category_set",
            primaryjoin="CustomEventCategory.category_set_id == CustomEventCategorySet.id",
        )
