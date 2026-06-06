from __future__ import annotations

from flask_security import current_user
from sqlalchemy import and_, func, select
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declared_attr, validates

from project.application.read_models.event_read_model import (
    AdminUnitReadModel,
    EventDateDefinitionReadModel,
    EventReadModel,
    OrganizerReadModel,
)
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.extensions import db
from project.models.event_category import CustomEventCategory, EventCategory
from project.models.event_date import EventDate, EventDateDefinition
from project.models.event_generated import EventGeneratedMixin
from project.models.event_organizer import EventOrganizer
from project.models.event_reference import EventReference
from project.models.event_reference_request import EventReferenceRequest
from project.models.functions import create_tsvector
from project.models.image import Image
from project.utils import make_check_violation


class Event(db.Model, EventGeneratedMixin):
    @declared_attr
    def __ts_vector__(cls):
        return create_tsvector((cls.name, "A"), (cls.tags, "B"), (cls.description, "C"))

    @classmethod
    def from_aggregate(cls, aggregate: EventAggregate) -> Event:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: EventAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.name = aggregate.name
        self.organizer_id = aggregate.organizer_id
        self.event_place_id = aggregate.event_place_id
        self.status = aggregate.status
        self.public_status = aggregate.public_status
        self.description = aggregate.description
        self.external_link = aggregate.external_link
        self.ticket_link = aggregate.ticket_link
        self.tags = aggregate.tags
        self.internal_tags = aggregate.internal_tags
        self.kid_friendly = aggregate.kid_friendly
        self.accessible_for_free = aggregate.accessible_for_free
        self.age_from = aggregate.age_from
        self.age_to = aggregate.age_to
        self.registration_required = aggregate.registration_required
        self.booked_up = aggregate.booked_up
        self.expected_participants = aggregate.expected_participants
        self.price_info = aggregate.price_info
        self.target_group_origin = aggregate.target_group_origin
        self.attendance_mode = aggregate.attendance_mode
        self.previous_start_date = aggregate.previous_start_date
        self.category_ids = aggregate.category_ids
        self.custom_category_ids = aggregate.custom_category_ids
        self.rating = aggregate.rating
        self.co_organizer_ids = aggregate.co_organizer_ids

        # Date defintions
        date_definitions_aggregate_length = (
            len(aggregate.date_definitions) if aggregate.date_definitions else 0
        )
        date_definitions_model_length = (
            len(self.date_definitions) if self.date_definitions else 0
        )

        for i in range(date_definitions_aggregate_length):
            if i < date_definitions_model_length:
                date_definition = self.date_definitions[i]
            else:
                date_definition = EventDateDefinition()
                self.date_definitions.append(date_definition)
            date_definition.fill_from_value_object(aggregate.date_definitions[i])

        for i in range(
            date_definitions_aggregate_length, date_definitions_model_length
        ):
            self.date_definitions.pop()

        # Dates
        aggregate_dates = aggregate.dates or []
        existing_dates_by_id = {d.id: d for d in self.dates if d.id}
        aggregate_date_ids = {e.id for e in aggregate_dates if e.id and e.id > 0}

        # Remove dates no longer in aggregate
        self.dates[:] = [d for d in self.dates if d.id in aggregate_date_ids]

        for entity in aggregate_dates:
            entity_id = entity.id if entity.id and entity.id > 0 else None
            if entity_id and entity_id in existing_dates_by_id:
                date = existing_dates_by_id[entity_id]
            else:
                date = EventDate()
                self.dates.append(date)
            date.fill_from_entity(entity)

        # Photo
        if aggregate.photo:
            if not self.photo:
                self.photo = Image()
            self.photo.fill_from_entity(aggregate.photo)
        else:
            self.photo = None

        return self

    @classmethod
    def to_aggregate(cls, model: Event) -> EventAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = EventAggregate.model_construct(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            name=model.name,
            organizer_id=model.organizer_id,
            event_place_id=model.event_place_id,
            status=model.status,
            public_status=model.public_status,
            description=model.description,
            external_link=model.external_link,
            ticket_link=model.ticket_link,
            tags=model.tags,
            internal_tags=model.internal_tags,
            kid_friendly=model.kid_friendly,
            accessible_for_free=model.accessible_for_free,
            age_from=model.age_from,
            age_to=model.age_to,
            registration_required=model.registration_required,
            booked_up=model.booked_up,
            expected_participants=model.expected_participants,
            price_info=model.price_info,
            target_group_origin=model.target_group_origin,
            attendance_mode=model.attendance_mode,
            previous_start_date=model.previous_start_date,
            category_ids=[c.id for c in model.categories],
            custom_category_ids=[c.id for c in model.custom_categories],
            rating=model.rating,
            co_organizer_ids=[c.id for c in model.co_organizers],
            photo=model.photo.to_entity() if model.photo else None,
        )

        # Date defintions
        aggregate.date_definitions = [
            d.to_value_object() for d in model.date_definitions
        ]

        # Dates
        aggregate.dates = [d.to_entity() for d in model.dates]

        return aggregate

    @classmethod
    def to_read_model(cls, model: Event) -> EventReadModel:
        if model is None:  # pragma: no cover
            return None

        return EventReadModel(
            id=model.id,
            name=model.name,
            is_recurring=model.is_recurring,
            admin_unit=AdminUnitReadModel(
                id=model.admin_unit.id, name=model.admin_unit.name
            ),
            organizer=OrganizerReadModel(
                id=model.organizer.id, name=model.organizer.name
            ),
            min_start_definition=EventDateDefinitionReadModel(
                start=model.min_start_definition.start,
                end=model.min_start_definition.end,
                allday=model.min_start_definition.allday,
                recurrence_rule=model.min_start_definition.recurrence_rule,
            ),
        )

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
        self.co_organizers = (
            EventOrganizer.query.filter(EventOrganizer.id.in_(value)).all()
            if value
            else []
        )

    @property
    def category_ids(self):  # pragma: no cover
        return [c.id for c in self.categories]

    @category_ids.setter
    def category_ids(self, value):  # pragma: no cover
        self.categories = (
            EventCategory.query.filter(EventCategory.id.in_(value)).all()
            if value
            else []
        )

    @property
    def custom_category_ids(self):  # pragma: no cover
        return [c.id for c in self.custom_categories]

    @custom_category_ids.setter
    def custom_category_ids(self, value):  # pragma: no cover
        self.custom_categories = (
            CustomEventCategory.query.filter(CustomEventCategory.id.in_(value)).all()
            if value
            else []
        )

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
