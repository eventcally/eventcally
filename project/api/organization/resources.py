from project import rest_api, api_docs
from flask_apispec import marshal_with, doc, use_kwargs
from flask_apispec.views import MethodResource
from project.api.organization.schemas import (
    OrganizationSchema,
    OrganizationListRequestSchema,
    OrganizationListResponseSchema,
)
from project.models import AdminUnit
from project.api.event_date.schemas import (
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.api.event.schemas import (
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.api.organizer.schemas import (
    OrganizerListRequestSchema,
    OrganizerListResponseSchema,
)
from project.api.place.schemas import PlaceListRequestSchema, PlaceListResponseSchema
from project.services.event import get_event_dates_query, get_events_query
from project.services.event_search import EventSearchParams
from project.services.admin_unit import (
    get_admin_unit_query,
    get_organizer_query,
    get_place_query,
)


class OrganizationResource(MethodResource):
    @doc(tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    def get(self, id):
        return AdminUnit.query.get_or_404(id)


class OrganizationByShortNameResource(MethodResource):
    @doc(tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    def get(self, short_name):
        return AdminUnit.query.filter(AdminUnit.short_name == short_name).first_or_404()


class OrganizationEventDateSearchResource(MethodResource):
    @doc(tags=["Organizations", "Event Dates"])
    @use_kwargs(EventDateSearchRequestSchema, location=("query"))
    @marshal_with(EventDateSearchResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request()
        params.admin_unit_id = admin_unit.id

        pagination = get_event_dates_query(params).paginate()
        return pagination


class OrganizationEventSearchResource(MethodResource):
    @doc(tags=["Organizations", "Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request()
        params.admin_unit_id = admin_unit.id

        pagination = get_events_query(params).paginate()
        return pagination


class OrganizationListResource(MethodResource):
    @doc(tags=["Organizations"])
    @use_kwargs(OrganizationListRequestSchema, location=("query"))
    @marshal_with(OrganizationListResponseSchema)
    def get(self, **kwargs):
        keyword = kwargs["keyword"] if "keyword" in kwargs else None
        pagination = get_admin_unit_query(keyword).paginate()
        return pagination


class OrganizationOrganizerListResource(MethodResource):
    @doc(tags=["Organizations", "Organizers"])
    @use_kwargs(OrganizerListRequestSchema, location=("query"))
    @marshal_with(OrganizerListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_organizer_query(admin_unit.id, name).paginate()
        return pagination


class OrganizationPlaceListResource(MethodResource):
    @doc(tags=["Organizations", "Places"])
    @use_kwargs(PlaceListRequestSchema, location=("query"))
    @marshal_with(PlaceListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_place_query(admin_unit.id, name).paginate()
        return pagination


rest_api.add_resource(OrganizationResource, "/organizations/<int:id>")
api_docs.register(OrganizationResource)

rest_api.add_resource(
    OrganizationByShortNameResource, "/organizations/<string:short_name>"
)
api_docs.register(OrganizationByShortNameResource)

rest_api.add_resource(
    OrganizationEventDateSearchResource,
    "/organizations/<int:id>/event_dates/search",
)
api_docs.register(OrganizationEventDateSearchResource)

rest_api.add_resource(
    OrganizationEventSearchResource, "/organizations/<int:id>/events/search"
)
api_docs.register(OrganizationEventSearchResource)

rest_api.add_resource(OrganizationListResource, "/organizations")
api_docs.register(OrganizationListResource)

rest_api.add_resource(
    OrganizationOrganizerListResource, "/organizations/<int:id>/organizers"
)
api_docs.register(OrganizationOrganizerListResource)

rest_api.add_resource(
    OrganizationPlaceListResource,
    "/organizations/<int:id>/places",
)
api_docs.register(OrganizationPlaceListResource)
