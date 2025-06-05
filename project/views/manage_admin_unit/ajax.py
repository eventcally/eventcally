from sqlalchemy import func

from project import db
from project.models.admin_unit import AdminUnit
from project.models.event_organizer import EventOrganizer
from project.models.event_place import EventPlace
from project.modular.ajax import AjaxModelLoader
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.services.admin_unit import get_admin_unit_query
from project.services.search_params import AdminUnitSearchParams
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


class OrganizationAjaxModelLoader(AjaxModelLoader):
    def __init__(self, **options):
        self.for_reference_request = options.pop("for_reference_request", False)
        options["fields"] = [AdminUnit.name]
        super().__init__(db.session, AdminUnit, **options)

    def get_pagination(self, term):
        params = AdminUnitSearchParams()
        params.keyword = term
        params.include_unverified = current_admin_unit.can_verify_other

        if self.for_reference_request:
            params.reference_request_for_admin_unit_id = current_admin_unit.id

        pagination = get_admin_unit_query(params).paginate()
        return pagination
