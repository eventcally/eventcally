from flask_apispec import doc, marshal_with, use_kwargs
from flask_babelex import gettext
from sqlalchemy import and_

from project import db
from project.access import (
    access_or_401,
    can_verify_admin_unit,
    get_admin_unit_for_manage_or_404,
    login_api_user,
    login_api_user_or_401,
)
from project.api import add_api_resource
from project.api.event.resources import api_can_read_private_events
from project.api.event.schemas import (
    EventIdSchema,
    EventListRequestSchema,
    EventListResponseSchema,
    EventPostRequestSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.api.event_date.schemas import (
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.api.event_list.schemas import (
    EventListCreateRequestSchema,
    EventListIdSchema,
    EventListListRequestSchema,
    EventListListResponseSchema,
    EventListStatusListResponseSchema,
)
from project.api.event_reference.schemas import (
    EventReferenceListRequestSchema,
    EventReferenceListResponseSchema,
)
from project.api.organization.schemas import (
    OrganizationListRequestSchema,
    OrganizationListResponseSchema,
    OrganizationSchema,
)
from project.api.organization_invitation.schemas import (
    OrganizationInvitationCreateRequestSchema,
    OrganizationInvitationIdSchema,
    OrganizationInvitationListRequestSchema,
    OrganizationInvitationListResponseSchema,
)
from project.api.organization_relation.schemas import (
    OrganizationRelationCreateRequestSchema,
    OrganizationRelationIdSchema,
    OrganizationRelationListRequestSchema,
    OrganizationRelationListResponseSchema,
)
from project.api.organizer.schemas import (
    OrganizerIdSchema,
    OrganizerListRequestSchema,
    OrganizerListResponseSchema,
    OrganizerPostRequestSchema,
)
from project.api.place.schemas import (
    PlaceIdSchema,
    PlaceListRequestSchema,
    PlaceListResponseSchema,
    PlacePostRequestSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AdminUnit, Event, PublicStatus
from project.oauth2 import require_oauth
from project.services.admin_unit import (
    get_admin_unit_invitation_query,
    get_admin_unit_query,
    get_event_list_query,
    get_event_list_status_query,
    get_organizer_query,
    get_place_query,
)
from project.services.event import get_event_dates_query, get_events_query, insert_event
from project.services.event_search import EventSearchParams
from project.services.reference import (
    get_reference_incoming_query,
    get_reference_outgoing_query,
    get_relation_outgoing_query,
)
from project.views.utils import send_mail


class OrganizationResource(BaseResource):
    @doc(summary="Get organization", tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    @require_oauth(optional=True)
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
    @require_oauth(optional=True)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request()
        params.admin_unit_id = admin_unit.id
        params.can_read_private_events = api_can_read_private_events(admin_unit)

        pagination = get_event_dates_query(params).paginate()
        return pagination


class OrganizationEventSearchResource(BaseResource):
    @doc(summary="Search for events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_oauth(optional=True)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request()
        params.admin_unit_id = admin_unit.id
        params.can_read_private_events = api_can_read_private_events(admin_unit)

        pagination = get_events_query(params).paginate()
        return pagination


class OrganizationEventListResource(BaseResource):
    @doc(summary="List events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    @require_oauth(optional=True)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        event_filter = Event.admin_unit_id == admin_unit.id

        if not api_can_read_private_events(admin_unit):
            event_filter = and_(
                event_filter,
                Event.public_status == PublicStatus.published,
                AdminUnit.is_verified,
            )

        pagination = Event.query.join(Event.admin_unit).filter(event_filter).paginate()
        return pagination

    @doc(
        summary="Add new event",
        tags=["Organizations", "Events"],
        security=[{"oauth2": ["event:write"]}],
    )
    @use_kwargs(EventPostRequestSchema, location="json", apply=False)
    @marshal_with(EventIdSchema, 201)
    @require_oauth("event:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "event:create")

        event = self.create_instance(
            EventPostRequestSchema, admin_unit_id=admin_unit.id
        )
        insert_event(event)
        db.session.commit()

        return event, 201


class OrganizationListResource(BaseResource):
    @doc(summary="List organizations", tags=["Organizations"])
    @use_kwargs(OrganizationListRequestSchema, location=("query"))
    @marshal_with(OrganizationListResponseSchema)
    @require_oauth(optional=True)
    def get(self, **kwargs):
        keyword = kwargs["keyword"] if "keyword" in kwargs else None

        login_api_user()
        include_unverified = can_verify_admin_unit()

        pagination = get_admin_unit_query(keyword, include_unverified).paginate()
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

    @doc(
        summary="Add new organizer",
        tags=["Organizations", "Organizers"],
        security=[{"oauth2": ["organizer:write"]}],
    )
    @use_kwargs(OrganizerPostRequestSchema, location="json", apply=False)
    @marshal_with(OrganizerIdSchema, 201)
    @require_oauth("organizer:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "organizer:create")

        organizer = self.create_instance(
            OrganizerPostRequestSchema, admin_unit_id=admin_unit.id
        )
        db.session.add(organizer)
        db.session.commit()

        return organizer, 201


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
    @use_kwargs(PlacePostRequestSchema, location="json", apply=False)
    @marshal_with(PlaceIdSchema, 201)
    @require_oauth("place:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "place:create")

        place = self.create_instance(
            PlacePostRequestSchema, admin_unit_id=admin_unit.id
        )
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


class OrganizationOutgoingRelationListResource(BaseResource):
    @doc(
        summary="List outgoing relations of organization",
        tags=["Organizations", "Organization Relations"],
        security=[{"oauth2": ["organization:read"]}],
    )
    @use_kwargs(OrganizationRelationListRequestSchema, location=("query"))
    @marshal_with(OrganizationRelationListResponseSchema)
    @require_api_access("organization:read")
    def get(self, id, **kwargs):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        pagination = get_relation_outgoing_query(admin_unit).paginate()
        return pagination

    @doc(
        summary="Add new outgoing relation",
        tags=["Organizations", "Organization Relations"],
        security=[{"oauth2": ["organization:write"]}],
    )
    @use_kwargs(OrganizationRelationCreateRequestSchema, location="json", apply=False)
    @marshal_with(OrganizationRelationIdSchema, 201)
    @require_api_access("organization:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        relation = self.create_instance(
            OrganizationRelationCreateRequestSchema, source_admin_unit_id=admin_unit.id
        )
        db.session.add(relation)
        db.session.commit()

        return relation, 201


class OrganizationOrganizationInvitationListResource(BaseResource):
    @doc(
        summary="List organization invitations of organization",
        tags=["Organizations", "Organization Invitations"],
        security=[{"oauth2": ["organization:read"]}],
    )
    @use_kwargs(OrganizationInvitationListRequestSchema, location=("query"))
    @marshal_with(OrganizationInvitationListResponseSchema)
    @require_api_access("organization:read")
    def get(self, id, **kwargs):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        pagination = get_admin_unit_invitation_query(admin_unit).paginate()
        return pagination

    @doc(
        summary="Add new organization invitation",
        tags=["Organizations", "Organization Invitations"],
        security=[{"oauth2": ["organization:write"]}],
    )
    @use_kwargs(OrganizationInvitationCreateRequestSchema, location="json", apply=False)
    @marshal_with(OrganizationInvitationIdSchema, 201)
    @require_api_access("organization:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        invitation = self.create_instance(
            OrganizationInvitationCreateRequestSchema, admin_unit_id=admin_unit.id
        )
        db.session.add(invitation)
        db.session.commit()

        send_mail(
            invitation.email,
            gettext("You have received an invitation"),
            "organization_invitation_notice",
            invitation=invitation,
        )

        return invitation, 201


class OrganizationEventListListResource(BaseResource):
    @doc(
        summary="List event lists of organization",
        tags=["Organizations", "Event Lists"],
    )
    @use_kwargs(EventListListRequestSchema, location=("query"))
    @marshal_with(EventListListResponseSchema)
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_event_list_query(admin_unit.id, name).paginate()
        return pagination

    @doc(
        summary="Add new event list",
        tags=["Organizations", "Event Lists"],
        security=[{"oauth2": ["eventlist:write"]}],
    )
    @use_kwargs(EventListCreateRequestSchema, location="json", apply=False)
    @marshal_with(EventListIdSchema, 201)
    @require_api_access("eventlist:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        event_list = self.create_instance(
            EventListCreateRequestSchema, admin_unit_id=admin_unit.id
        )
        db.session.add(event_list)
        db.session.commit()

        return event_list, 201


class OrganizationEventListStatusListResource(BaseResource):
    @doc(
        summary="List event lists of organization with status",
        tags=["Organizations", "Event Lists"],
    )
    @use_kwargs(EventListListRequestSchema, location=("query"))
    @marshal_with(EventListStatusListResponseSchema)
    def get(self, id, event_id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_event_list_status_query(
            admin_unit.id, event_id, name
        ).paginate()
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
add_api_resource(
    OrganizationEventListResource,
    "/organizations/<int:id>/events",
    "api_v1_organization_event_list",
)
add_api_resource(
    OrganizationEventListListResource,
    "/organizations/<int:id>/event-lists",
    "api_v1_organization_event_list_list",
)
add_api_resource(
    OrganizationEventListStatusListResource,
    "/organizations/<int:id>/event-lists/status/<int:event_id>",
    "api_v1_organization_event_list_status_list",
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
add_api_resource(
    OrganizationOutgoingRelationListResource,
    "/organizations/<int:id>/relations/outgoing",
    "api_v1_organization_outgoing_relation_list",
)
add_api_resource(
    OrganizationOrganizationInvitationListResource,
    "/organizations/<int:id>/organization-invitations",
    "api_v1_organization_organization_invitation_list",
)
