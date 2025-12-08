from flask_security import current_user
from sqlalchemy import and_, func, select
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr, validates

from project import db
from project.models.event_date import EventDate, EventDateDefinition
from project.models.event_generated import EventGeneratedMixin
from project.models.event_organizer import EventOrganizer
from project.models.event_reference import EventReference
from project.models.event_reference_request import EventReferenceRequest
from project.models.functions import create_tsvector
from project.utils import make_check_violation


class Event(db.Model, EventGeneratedMixin):
    @declared_attr
    def __ts_vector__(cls):
        return create_tsvector((cls.name, "A"), (cls.tags, "B"), (cls.description, "C"))

    @property
    def custom_categories_by_set(self):
        categories_by_set = {}
        for category in self.custom_categories:
            if category.category_set_id not in categories_by_set:
                categories_by_set[category.category_set_id] = []
            categories_by_set[category.category_set_id].append(category)
        return categories_by_set

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
