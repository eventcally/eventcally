from sqlalchemy import func

from project import db
from project.models.event_organizer import EventOrganizer
from project.models.event_place import EventPlace
from project.modular.ajax import AjaxModelLoader
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.utils import get_place_str
from project.views.utils import current_admin_unit


class EventOrganizerAjaxModelLoader(AjaxModelLoader):
    def __init__(self, **kwargs):
        kwargs["search_definitions"] = [SearchDefinition(EventOrganizer.name)]
        kwargs["sort_definitions"] = [
            SortDefinition(EventOrganizer.name, func=func.lower)
        ]
        super().__init__(db.session, EventOrganizer, **kwargs)

    def get_query(self):
        return (
            super()
            .get_query()
            .filter(EventOrganizer.admin_unit_id == current_admin_unit.id)
        )


class EventPlaceAjaxModelLoader(AjaxModelLoader):
    def __init__(self, **kwargs):
        kwargs["search_definitions"] = [SearchDefinition(EventPlace.name)]
        kwargs["sort_definitions"] = [SortDefinition(EventPlace.name, func=func.lower)]
        super().__init__(db.session, EventPlace, **kwargs)

    def get_query(self):
        return (
            super()
            .get_query()
            .filter(EventPlace.admin_unit_id == current_admin_unit.id)
        )

    def format_model(self, model):
        return get_place_str(model)
