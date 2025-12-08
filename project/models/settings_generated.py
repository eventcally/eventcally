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


class SettingsGeneratedMixin(TrackableMixin):
    __tablename__ = "settings"

    __model_name__ = "settings"
    __model_name_plural__ = "settings"
    __display_name__ = "Settings"
    __display_name_plural__ = "Settings"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def tos(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def legal_notice(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def contact(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def privacy(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def start_page(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def announcement(cls):
        return deferred(Column(UnicodeText(), nullable=True))

    @declared_attr
    def planning_external_calendars(cls):
        return deferred(Column(UnicodeText(), nullable=True))
