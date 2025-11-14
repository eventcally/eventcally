from project.models import EventCategory
from project.services.base_service import BaseService


class EventCategoryService(BaseService[EventCategory]):
    model_class = EventCategory

    def get_event_category(self, category_name) -> EventCategory | None:
        return self.repo.get_event_category_by_name(category_name)

    def upsert_event_category(self, category_name) -> EventCategory:
        category = self.get_event_category(category_name)

        if category is None:
            category = self.repo.create_event_category(category_name)

        return category
