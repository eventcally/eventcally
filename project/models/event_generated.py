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


class EventTargetGroupOrigin(IntEnum):
    both = 1
    tourist = 2
    resident = 3


class EventAttendanceMode(IntEnum):
    offline = 1
    online = 2
    mixed = 3


class EventPublicStatus(IntEnum):
    draft = 1
    published = 2
    planned = 3


class EventStatus(IntEnum):
    scheduled = 1
    cancelled = 2
    movedOnline = 3
    postponed = 4
    rescheduled = 5


class EventGeneratedMixin(TrackableMixin):
    __tablename__ = "event"

    __model_name__ = "event"
    __model_name_plural__ = "events"
    __display_name__ = "Event"
    __display_name_plural__ = "Events"

    @declared_attr
    def id(cls):
        return Column(Integer(), primary_key=True)

    @declared_attr
    def name(cls):
        return Column(Unicode(255), nullable=False)

    @declared_attr
    def external_link(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def description(cls):
        return Column(UnicodeText(), nullable=True)

    @declared_attr
    def ticket_link(cls):
        return Column(Unicode(255), nullable=True)

    @declared_attr
    def tags(cls):
        return Column(UnicodeText(), nullable=True)

    @declared_attr
    def internal_tags(cls):
        return Column(UnicodeText(), nullable=True)

    @declared_attr
    def kid_friendly(cls):
        return Column(Boolean(), nullable=True)

    @declared_attr
    def accessible_for_free(cls):
        return Column(Boolean(), nullable=True)

    @declared_attr
    def age_from(cls):
        return Column(Integer(), nullable=True)

    @declared_attr
    def age_to(cls):
        return Column(Integer(), nullable=True)

    @declared_attr
    def target_group_origin(cls):
        return Column(IntegerEnum(EventTargetGroupOrigin), nullable=True)

    @declared_attr
    def attendance_mode(cls):
        return Column(IntegerEnum(EventAttendanceMode), nullable=True)

    @declared_attr
    def registration_required(cls):
        return Column(Boolean(), nullable=True)

    @declared_attr
    def booked_up(cls):
        return Column(Boolean(), nullable=True)

    @declared_attr
    def expected_participants(cls):
        return Column(Integer(), nullable=True)

    @declared_attr
    def price_info(cls):
        return Column(UnicodeText(), nullable=True)

    @declared_attr
    def public_status(cls):
        return Column(
            IntegerEnum(EventPublicStatus),
            nullable=False,
            default=EventPublicStatus.published.value,
            server_default=str(EventPublicStatus.published.value),
        )

    @declared_attr
    def status(cls):
        return Column(IntegerEnum(EventStatus), nullable=True)

    @declared_attr
    def previous_start_date(cls):
        return Column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def rating(cls):
        return Column(Integer(), default=50, nullable=True)

    @declared_attr
    def admin_unit_id(cls):
        return Column(
            Integer(), ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
        )

    @declared_attr
    def organizer_id(cls):
        return Column(Integer(), ForeignKey("eventorganizer.id"), nullable=False)

    @declared_attr
    def event_place_id(cls):
        return Column(Integer(), ForeignKey("eventplace.id"), nullable=False)

    @declared_attr
    def photo_id(cls):
        return Column(
            Integer(), ForeignKey("image.id", ondelete="SET NULL"), nullable=True
        )

    @declared_attr
    def admin_unit(cls):
        return relationship(
            "AdminUnit",
            foreign_keys=[cls.admin_unit_id],
            back_populates="events",
        )

    @declared_attr
    def organizer(cls):
        return relationship(
            "EventOrganizer",
            foreign_keys=[cls.organizer_id],
            back_populates="events",
        )

    @declared_attr
    def event_place(cls):
        return relationship(
            "EventPlace",
            foreign_keys=[cls.event_place_id],
            back_populates="events",
        )

    @declared_attr
    def photo(cls):
        return relationship(
            "Image",
            foreign_keys=[cls.photo_id],
            uselist=False,
            single_parent=True,
            cascade="all, delete-orphan",
            back_populates="event",
        )

    @declared_attr
    def categories(cls):
        return relationship(
            "EventCategory",
            back_populates="events",
            secondary="event_eventcategories",
        )

    @declared_attr
    def custom_categories(cls):
        return relationship(
            "CustomEventCategory",
            back_populates="events",
            secondary="event_customeventcategories",
        )

    @declared_attr
    def co_organizers(cls):
        return relationship(
            "EventOrganizer",
            back_populates="co_organized_events",
            secondary="event_coorganizers",
        )

    @declared_attr
    def event_lists(cls):
        return relationship(
            "EventList",
            back_populates="events",
            secondary="event_eventlists",
        )

    @declared_attr
    def date_definitions(cls):
        return relationship(
            "EventDateDefinition",
            cascade="all, delete-orphan",
            back_populates="event",
            primaryjoin="EventDateDefinition.event_id == Event.id",
            order_by="EventDateDefinition.start",
        )

    @declared_attr
    def dates(cls):
        return relationship(
            "EventDate",
            cascade="all, delete-orphan",
            back_populates="event",
            primaryjoin="EventDate.event_id == Event.id",
        )

    @declared_attr
    def references(cls):
        return relationship(
            "EventReference",
            cascade="all, delete-orphan",
            back_populates="event",
            primaryjoin="EventReference.event_id == Event.id",
        )

    @declared_attr
    def reference_requests(cls):
        return relationship(
            "EventReferenceRequest",
            cascade="all, delete-orphan",
            back_populates="event",
            primaryjoin="EventReferenceRequest.event_id == Event.id",
        )

    @declared_attr
    def favored_by_users(cls):
        return relationship(
            "User",
            back_populates="favorite_events",
            secondary="user_favoriteevents",
        )
