from project.models import EventCategory
from project.repos.base_repo import BaseRepo


class EventCategoryRepo(BaseRepo[EventCategory]):
    model_class = EventCategory

    def get_event_category_by_name(self, category_name) -> EventCategory | None:
        return EventCategory.query.filter_by(name=category_name).first()

    def create_event_category(self, category_name) -> EventCategory:
        category = EventCategory(name=category_name)
        self.insert_object(category)
        return category
