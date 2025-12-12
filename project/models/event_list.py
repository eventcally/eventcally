from project import db
from project.models.association_tables.event_event_lists_generated import (
    EventEventListsGeneratedMixin,
)
from project.models.event_list_generated import EventListGeneratedMixin


class EventList(db.Model, EventListGeneratedMixin):
    pass


class EventEventLists(db.Model, EventEventListsGeneratedMixin):
    pass
