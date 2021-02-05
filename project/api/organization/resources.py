from project.api import add_api_resource
from flask_apispec import marshal_with, doc, use_kwargs
from project.api.resources import BaseResource
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
from project.api.event_reference.schemas import (
    EventReferenceListRequestSchema,
    EventReferenceListResponseSchema,
)
from project.services.reference import (
    get_reference_incoming_query,
    get_reference_outgoing_query,
)
from project.api.place.schemas import (
    PlaceListRequestSchema,
    PlaceListResponseSchema,
    PlaceIdSchema,
    PlacePostRequestSchema,
    PlacePostRequestLoadSchema,
)
from project.services.event import get_event_dates_query, get_events_query
from project.services.event_search import EventSearchParams
from project.services.admin_unit import (
    get_admin_unit_query,
    get_organizer_query,
    get_place_query,
)
from project.oauth2 import require_oauth
from authlib.integrations.flask_oauth2 import current_token
from project import db
from project.access import (
    access_or_401,
    get_admin_unit_for_manage_or_404,
    login_api_user_or_401,
)


class OrganizationResource(BaseResource):
    @doc(summary="Get organization", tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    def get(self, id):
        return AdminUnit.query.get_or_404(id)


class OrganizationEventDateSearchResource(BaseResource):
    @doc(
        summary="Search for event dates of organization",
        description="Includes events that organization is referencing.",
        tags=["Organizations", "Event Dates"],
    )
    @use_kwargs(EventDateSearchRequestSchema, location=("query"))
    @marshal_with(EventDateSearchResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request()
        params.admin_unit_id = admin_unit.id

        pagination = get_event_dates_query(params).paginate()
        return pagination


class OrganizationEventSearchResource(BaseResource):
    @doc(summary="Search for events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request()
        params.admin_unit_id = admin_unit.id

        pagination = get_events_query(params).paginate()
        return pagination


class OrganizationListResource(BaseResource):
    @doc(summary="List organizations", tags=["Organizations"])
    @use_kwargs(OrganizationListRequestSchema, location=("query"))
    @marshal_with(OrganizationListResponseSchema)
    def get(self, **kwargs):
        keyword = kwargs["keyword"] if "keyword" in kwargs else None
        pagination = get_admin_unit_query(keyword).paginate()
        return pagination


class OrganizationOrganizerListResource(BaseResource):
    @doc(
        summary="List organizers of organization", tags=["Organizations", "Organizers"]
    )
    @use_kwargs(OrganizerListRequestSchema, location=("query"))
    @marshal_with(OrganizerListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_organizer_query(admin_unit.id, name).paginate()
        return pagination


class OrganizationPlaceListResource(BaseResource):
    @doc(summary="List places of organization", tags=["Organizations", "Places"])
    @use_kwargs(PlaceListRequestSchema, location=("query"))
    @marshal_with(PlaceListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_place_query(admin_unit.id, name).paginate()
        return pagination

    @doc(
        summary="Add new place",
        tags=["Organizations", "Places"],
        security=[{"oauth2": ["place:write"]}],
    )
    @use_kwargs(PlacePostRequestSchema, location="json")
    @marshal_with(PlaceIdSchema, 201)
    @require_oauth("place:write")
    def post(self, id, **kwargs):
        login_api_user_or_401(current_token.user)
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "place:create")

        place = PlacePostRequestLoadSchema().load(kwargs, session=db.session)
        place.admin_unit_id = admin_unit.id
        db.session.add(place)
        db.session.commit()

        return place, 201


class OrganizationIncomingEventReferenceListResource(BaseResource):
    @doc(
        summary="List incoming event references of organization",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceListRequestSchema, location=("query"))
    @marshal_with(EventReferenceListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        pagination = get_reference_incoming_query(admin_unit).paginate()
        return pagination


class OrganizationOutgoingEventReferenceListResource(BaseResource):
    @doc(
        summary="List outgoing event references of organization",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceListRequestSchema, location=("query"))
    @marshal_with(EventReferenceListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        pagination = get_reference_outgoing_query(admin_unit).paginate()
        return pagination


add_api_resource(OrganizationResource, "/organizations/<int:id>", "api_v1_organization")
add_api_resource(
    OrganizationEventDateSearchResource,
    "/organizations/<int:id>/event-dates/search",
    "api_v1_organization_event_date_search",
)
add_api_resource(
    OrganizationEventSearchResource,
    "/organizations/<int:id>/events/search",
    "api_v1_organization_event_search",
)
add_api_resource(OrganizationListResource, "/organizations", "api_v1_organization_list")
add_api_resource(
    OrganizationOrganizerListResource,
    "/organizations/<int:id>/organizers",
    "api_v1_organization_organizer_list",
)
add_api_resource(
    OrganizationPlaceListResource,
    "/organizations/<int:id>/places",
    "api_v1_organization_place_list",
)
add_api_resource(
    OrganizationIncomingEventReferenceListResource,
    "/organizations/<int:id>/event-references/incoming",
    "api_v1_organization_incoming_event_reference_list",
)
add_api_resource(
    OrganizationOutgoingEventReferenceListResource,
    "/organizations/<int:id>/event-references/outgoing",
    "api_v1_organization_outgoing_event_reference_list",
)
