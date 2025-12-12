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
from project.models.mixins.trackable_mixin import TrackableMixin


class EventReferenceRequestReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class EventReferenceRequestRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4


class EventReferenceRequestGeneratedMixin(TrackableMixin):
    __tablename__ = "eventreferencerequest"
    __table_args__ = (UniqueConstraint("event_id", "admin_unit_id"),)

    __model_name__ = "event_reference_request"
    __model_name_plural__ = "event_reference_requests"
    __display_name__ = "Event reference request"
    __display_name_plural__ = "Event reference requests"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def review_status(cls):
        return Column(IntegerEnum(EventReferenceRequestReviewStatus), nullable=True)

    @declared_attr
    def rejection_reason(cls):
        return Column(IntegerEnum(EventReferenceRequestRejectionReason), nullable=True)

    @declared_attr
    def event_id(cls):
        return Column(
            Integer(), ForeignKey("event.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def event(cls):
        return relationship(
            "Event",
            foreign_keys=[cls.event_id],
            back_populates="reference_requests",
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="reference_requests",
        )
