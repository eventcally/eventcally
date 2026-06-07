from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.extensions import db
from project.models.event_date_definition_generated import (
    EventDateDefinitionGeneratedMixin,
)
from project.models.event_date_generated import EventDateGeneratedMixin
from project.models.functions import sanitize_allday_instance
from project.utils import make_check_violation


class EventDate(db.Model, EventDateGeneratedMixin):
    def fill_from_entity(self, entity: EventDateEntity):
        self.id = entity.id if entity.id and entity.id > 0 else None
        self.start = entity.start
        self.end = entity.end
        self.allday = entity.allday

    def to_entity(self) -> EventDateEntity:
        return EventDateEntity(
            id=self.id,
            start=self.start,
            end=self.end,
            allday=self.allday,
        )

    @hybrid_property
    def end_or_start(self):  # pragma: no cover
        return self.end if self.end else self.start

    @end_or_start.expression
    def end_or_start(cls):
        return func.coalesce(cls.end, cls.start)


@listens_for(EventDate, "before_insert")
@listens_for(EventDate, "before_update")
def purge_event_date(mapper, connect, self):
    sanitize_allday_instance(self)


class EventDateDefinition(db.Model, EventDateDefinitionGeneratedMixin):
    def fill_from_value_object(self, value_object: EventDateDefinitionValueObject):
        self.start = value_object.start
        self.end = value_object.end
        self.allday = value_object.allday
        self.recurrence_rule = value_object.recurrence_rule

    def to_value_object(self) -> EventDateDefinitionValueObject:
        return EventDateDefinitionValueObject(
            start=self.start,
            end=self.end,
            allday=self.allday,
            recurrence_rule=self.recurrence_rule,
        )

    def validate(self):
        if self.start and self.end:
            if self.start > self.end:
                raise make_check_violation("The start must be before the end.")

            max_end = self.start + relativedelta(days=180)
            if self.end > max_end:
                raise make_check_violation("An event can last a maximum of 180 days.")


@listens_for(EventDateDefinition, "before_insert")
@listens_for(EventDateDefinition, "before_update")
def before_saving_event_date_definition(mapper, connect, self):
    self.validate()
    sanitize_allday_instance(self)
