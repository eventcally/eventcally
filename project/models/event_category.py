from project import db
from project.models.association_tables.event_custom_event_categories_generated import (
    EventCustomEventCategoriesGeneratedMixin,
)
from project.models.association_tables.event_event_categories_generated import (
    EventEventCategoriesGeneratedMixin,
)
from project.models.custom_event_category_generated import (
    CustomEventCategoryGeneratedMixin,
)
from project.models.custom_event_category_set_generated import (
    CustomEventCategorySetGeneratedMixin,
)
from project.models.event_category_generated import EventCategoryGeneratedMixin


class EventCategory(db.Model, EventCategoryGeneratedMixin):
    pass


class EventEventCategories(db.Model, EventEventCategoriesGeneratedMixin):
    pass


class CustomEventCategorySet(db.Model, CustomEventCategorySetGeneratedMixin):
    pass

    @property
    def label_or_name(self):
        return self.label or self.name

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class CustomEventCategory(db.Model, CustomEventCategoryGeneratedMixin):
    pass

    @property
    def label_or_name(self):
        return self.label or self.name

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class EventCustomEventCategories(db.Model, EventCustomEventCategoriesGeneratedMixin):
    pass
