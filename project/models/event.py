from enum import IntEnum

from flask_security import current_user
from sqlalchemy import Column, Integer, and_, func, select
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship, validates

from project import db
from project.dbtypes import IntegerEnum
from project.models.event_date import EventDate, EventDateDefinition
from project.models.event_mixin import EventMixin
from project.models.event_organizer import EventOrganizer
from project.models.event_reference import EventReference
from project.models.event_reference_request import EventReferenceRequest
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class EventStatus(IntEnum):
    scheduled = 1
    cancelled = 2
    movedOnline = 3
    postponed = 4
    rescheduled = 5


class PublicStatus(IntEnum):
    draft = 1
    published = 2
    planned = 3


class Event(db.Model, TrackableMixin, EventMixin):
    __tablename__ = "event"
    id = Column(Integer(), primary_key=True)

    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=False
    )
    organizer = db.relationship(
        "EventOrganizer",
        uselist=False,
        backref=backref("events", lazy=True),
    )
    event_place_id = db.Column(
        db.Integer,
        db.ForeignKey("eventplace.id"),
        nullable=False,
    )
    event_place = db.relationship(
        "EventPlace",
        uselist=False,
        backref=backref("events", lazy=True),
    )

    categories = relationship("EventCategory", secondary="event_eventcategories")
    co_organizers = relationship(
        "EventOrganizer",
        secondary="event_coorganizers",
        backref=backref("co_organized_events", lazy=True),
    )
    event_lists = relationship(
        "EventList",
        secondary="event_eventlists",
        backref=backref("events", lazy=True),
    )

    public_status = Column(
        IntegerEnum(PublicStatus),
        nullable=False,
        default=PublicStatus.published.value,
        server_default=str(PublicStatus.published.value),
    )
    status = Column(IntegerEnum(EventStatus))
    previous_start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    rating = Column(Integer(), default=50)

    @property
    def min_start_definition(self):
        if self.date_definitions:
            return min(self.date_definitions, key=lambda d: d.start)
        else:
            return None

    @hybrid_property
    def min_start(self):
        if self.date_definitions:
            return min(d.start for d in self.date_definitions)
        else:
            return None

    @min_start.expression
    def min_start(cls):
        return (
            select(EventDateDefinition.start)
            .where(EventDateDefinition.event_id == cls.id)
            .order_by(EventDateDefinition.start)
            .limit(1)
            .scalar_subquery()
        )

    @hybrid_property
    def is_recurring(self):
        if self.date_definitions:
            return any(d.recurrence_rule for d in self.date_definitions)
        else:
            return False

    @is_recurring.expression
    def is_recurring(cls):
        return (
            select(func.count())
            .select_from(EventDateDefinition.__table__)
            .where(
                and_(
                    EventDateDefinition.event_id == cls.id,
                    func.coalesce(EventDateDefinition.recurrence_rule, "") != "",
                )
            )
            .scalar_subquery()
        ) > 0

    date_definitions = relationship(
        "EventDateDefinition",
        order_by="EventDateDefinition.start",
        backref=backref("event", lazy=False),
        cascade="all, delete-orphan",
    )

    dates = relationship(
        "EventDate", backref=backref("event", lazy=False), cascade="all, delete-orphan"
    )

    @hybrid_property
    def number_of_dates(self):  # pragma: no cover
        return len(self.dates)

    @number_of_dates.expression
    def number_of_dates(cls):
        return (
            select(func.count()).where(EventDate.event_id == cls.id).scalar_subquery()
        )

    @hybrid_property
    def min_date_start(self):  # pragma: no cover
        if self.dates:
            return min(d.start for d in self.dates)
        else:
            return None

    @min_date_start.expression
    def min_date_start(cls):
        return (
            select(EventDate.start)
            .where(EventDate.event_id == cls.id)
            .order_by(EventDate.start)
            .limit(1)
            .scalar_subquery()
        )

    @hybrid_property
    def max_date_end(self):  # pragma: no cover
        if self.dates:
            return max(d.end_or_start for d in self.dates)
        else:
            return None

    @max_date_end.expression
    def max_date_end(cls):
        return (
            select(EventDate.start)
            .where(EventDate.event_id == cls.id)
            .order_by(EventDate.end_or_start.desc())
            .limit(1)
            .scalar_subquery()
        )

    references = relationship(
        "EventReference",
        backref=backref("event", lazy=False),
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def number_of_references(self):  # pragma: no cover
        return len(self.references)

    @number_of_references.expression
    def number_of_references(cls):
        return (
            select(func.count())
            .where(EventReference.event_id == cls.id)
            .scalar_subquery()
        )

    reference_requests = relationship(
        "EventReferenceRequest",
        backref=backref("event", lazy=False),
        cascade="all, delete-orphan",
    )

    @hybrid_property
    def number_of_reference_requests(self):  # pragma: no cover
        return len(self.reference_requests)

    @number_of_reference_requests.expression
    def number_of_reference_requests(cls):
        return (
            select(func.count())
            .where(EventReferenceRequest.event_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def category(self):
        if self.categories:
            return self.categories[0]
        else:
            return None

    @property
    def co_organizer_ids(self):  # pragma: no cover
        return [c.id for c in self.co_organizers]

    @co_organizer_ids.setter
    def co_organizer_ids(self, value):  # pragma: no cover
        self.co_organizers = EventOrganizer.query.filter(
            EventOrganizer.id.in_(value)
        ).all()

    def has_multiple_dates(self) -> bool:
        return self.is_recurring or len(self.date_definitions) > 1

    def is_favored_by_current_user(self) -> bool:
        if not current_user or not current_user.is_authenticated:
            return False

        from project.services.user import has_favorite_event

        return has_favorite_event(current_user.id, self.id)

    def validate(self):
        if self.organizer and self.organizer.admin_unit_id != self.admin_unit_id:
            raise make_check_violation("Invalid organizer.")

        if self.co_organizers:
            for co_organizer in self.co_organizers:
                if (
                    co_organizer.admin_unit_id != self.admin_unit_id
                    or co_organizer.id == self.organizer_id
                ):
                    raise make_check_violation("Invalid co-organizer.")

        if self.event_place and self.event_place.admin_unit_id != self.admin_unit_id:
            raise make_check_violation("Invalid place.")

        if not self.date_definitions or len(self.date_definitions) == 0:
            raise make_check_violation("At least one date defintion is required.")

    def __str__(self):
        return self.name or super().__str__()

    @validates("tags")
    def validate_tags(self, key, value):
        return value.replace(" ", "") if value else None

    @validates("internal_tags")
    def validate_internal_tags(self, key, value):
        return value.replace(" ", "") if value else None


@listens_for(Event, "before_insert")
@listens_for(Event, "before_update")
def before_saving_event(mapper, connect, self):
    self.validate()
