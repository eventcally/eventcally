from project.application.queries import (
    GetEventOrganizerRefQuery,
    GetEventPlaceRefQuery,
    LookupEventOrganizersQuery,
    LookupEventPlacesQuery,
)
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.modular.ajax import QueryAjaxLoader
from project.shared.utils import get_place_str


class EventOrganizerAjaxModelLoader(QueryAjaxLoader):
    def get_lookup_query(self, term, page_request):
        return LookupEventOrganizersQuery(
            admin_unit_id=current_admin_unit.id, term=term, page=page_request
        )

    def get_one_query(self, pk):
        return GetEventOrganizerRefQuery(admin_unit_id=current_admin_unit.id, id=pk)


class EventPlaceAjaxModelLoader(QueryAjaxLoader):
    def get_lookup_query(self, term, page_request):
        return LookupEventPlacesQuery(
            admin_unit_id=current_admin_unit.id, term=term, page=page_request
        )

    def get_one_query(self, pk):
        return GetEventPlaceRefQuery(admin_unit_id=current_admin_unit.id, id=pk)

    def format_model(self, model):
        return get_place_str(model)
