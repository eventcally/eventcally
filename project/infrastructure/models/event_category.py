from project.infrastructure.extensions import db
from project.infrastructure.models.association_tables.event_custom_event_categories_generated import (
    EventCustomEventCategoriesGeneratedMixin,
)
from project.infrastructure.models.association_tables.event_event_categories_generated import (
    EventEventCategoriesGeneratedMixin,
)
from project.infrastructure.models.custom_event_category_generated import (
    CustomEventCategoryGeneratedMixin,
)
from project.infrastructure.models.custom_event_category_set_generated import (
    CustomEventCategorySetGeneratedMixin,
)
from project.infrastructure.models.event_category_generated import (
    EventCategoryGeneratedMixin,
)


class EventCategory(db.Model, EventCategoryGeneratedMixin):
    pass


class EventEventCategories(db.Model, EventEventCategoriesGeneratedMixin):
    pass


class CustomEventCategorySet(db.Model, CustomEventCategorySetGeneratedMixin):
    pass

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class CustomEventCategory(db.Model, CustomEventCategoryGeneratedMixin):
    pass

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class EventCustomEventCategories(db.Model, EventCustomEventCategoriesGeneratedMixin):
    pass
