from flask import abort, request
from flask_apispec import doc, marshal_with, use_kwargs
from flask_babel import gettext
from sqlalchemy import and_

from project import db
from project.access import (
    access_or_401,
    can_request_event_reference,
    can_verify_admin_unit,
    get_admin_unit_for_manage_or_404,
    login_api_user,
    login_api_user_or_401,
)
from project.api import add_api_resource
from project.api.custom_widget.schemas import (
    CustomWidgetIdSchema,
    CustomWidgetListRequestSchema,
    CustomWidgetListResponseSchema,
    CustomWidgetPostRequestSchema,
)
from project.api.event.resources import api_can_read_private_events
from project.api.event.schemas import (
    EventIdSchema,
    EventImportRequestSchema,
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
    EventReferenceCreateRequestSchema,
    EventReferenceIdSchema,
    EventReferenceListRequestSchema,
    EventReferenceListResponseSchema,
)
from project.api.event_reference_request.schemas import (
    EventReferenceRequestIdSchema,
    EventReferenceRequestListRequestSchema,
    EventReferenceRequestListResponseSchema,
    EventReferenceRequestPostRequestSchema,
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
    OrganizationRelationSchema,
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
from project.models.admin_unit import AdminUnitInvitation, AdminUnitRelation
from project.services.admin_unit import (
    get_admin_unit_invitation_query,
    get_admin_unit_query,
    get_custom_widget_query,
    get_event_list_query,
    get_event_list_status_query,
    get_organizer_query,
    get_place_query,
)
from project.services.event import get_event_dates_query, get_events_query, insert_event
from project.services.importer.event_importer import EventImporter
from project.services.reference import (
    get_reference_incoming_query,
    get_reference_outgoing_query,
    get_reference_requests_incoming_query,
    get_reference_requests_outgoing_query,
    get_relation_outgoing_query,
)
from project.services.search_params import (
    AdminUnitSearchParams,
    EventPlaceSearchParams,
    EventReferenceRequestSearchParams,
    EventReferenceSearchParams,
    EventSearchParams,
    OrganizerSearchParams,
    TrackableSearchParams,
)
from project.views.reference_request import (
    handle_request_according_to_relation,
    send_reference_request_mails,
)
from project.views.utils import get_current_admin_unit_for_api, send_mail_async


class OrganizationResource(BaseResource):
    @doc(summary="Get organization", tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    @require_api_access()
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
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.include_admin_unit_references = True
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        params.can_read_private_events = api_can_read_private_events(admin_unit)

        pagination = get_event_dates_query(params).paginate()
        return pagination


class OrganizationEventSearchResource(BaseResource):
    @doc(summary="Search for events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        params.can_read_private_events = api_can_read_private_events(admin_unit)

        pagination = get_events_query(params).paginate()
        return pagination


class OrganizationEventListResource(BaseResource):
    @doc(summary="List events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        params = EventSearchParams()
        params.load_from_request(**kwargs)

        admin_unit = AdminUnit.query.get_or_404(id)
        event_filter = Event.admin_unit_id == admin_unit.id

        if not api_can_read_private_events(admin_unit):
            event_filter = and_(
                event_filter,
                Event.public_status == PublicStatus.published,
                AdminUnit.is_verified,
            )

        query = Event.query.join(Event.admin_unit).filter(event_filter)
        query = params.get_trackable_query(query, Event)
        query = params.get_trackable_order_by(query, Event)
        query = query.order_by(Event.min_start)

        return query.paginate()

    @doc(
        summary="Add new event",
        tags=["Organizations", "Events"],
    )
    @use_kwargs(EventPostRequestSchema, location="json", apply=False)
    @marshal_with(EventIdSchema, 201)
    @require_api_access("event:write")
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


class OrganizationEventImportResource(BaseResource):
    @doc(summary="Import event for organization", tags=["Organizations", "Events"])
    @use_kwargs(EventImportRequestSchema, location="json", apply=False)
    @marshal_with(EventIdSchema, 201)
    @require_api_access("event:write")
    def post(self, id, **kwargs):
        login_api_user_or_401()
        admin_unit = AdminUnit.query.get_or_404(id)
        access_or_401(admin_unit, "event:create")

        import_request = EventImportRequestSchema().load(request.json)

        try:
            importer = EventImporter(admin_unit.id)

            with db.session.no_autoflush:
                # deepcode ignore Ssrf: url sanitized in importer
                event = importer.load_event_from_url(import_request["url"])
        except Exception:
            abort(422)

        event.public_status = import_request["public_status"]
        insert_event(event)
        db.session.commit()

        return event, 201


class OrganizationListResource(BaseResource):
    @doc(
        summary="List organizations",
        tags=["Organizations"],
    )
    @use_kwargs(OrganizationListRequestSchema, location=("query"))
    @marshal_with(OrganizationListResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        login_api_user()
        include_unverified = can_verify_admin_unit()
        reference_request_for_admin_unit_id = None

        if "for_reference_request" in request.args:
            admin_unit = get_current_admin_unit_for_api()

            if admin_unit:
                reference_request_for_admin_unit_id = admin_unit.id

        params = AdminUnitSearchParams()
        params.load_from_request(**kwargs)
        params.include_unverified = include_unverified
        params.reference_request_for_admin_unit_id = reference_request_for_admin_unit_id
        pagination = get_admin_unit_query(params).paginate()
        return pagination


class OrganizationOrganizerListResource(BaseResource):
    @doc(
        summary="List organizers of organization", tags=["Organizations", "Organizers"]
    )
    @use_kwargs(OrganizerListRequestSchema, location=("query"))
    @marshal_with(OrganizerListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = OrganizerSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        pagination = get_organizer_query(params).paginate()
        return pagination

    @doc(
        summary="Add new organizer",
        tags=["Organizations", "Organizers"],
    )
    @use_kwargs(OrganizerPostRequestSchema, location="json", apply=False)
    @marshal_with(OrganizerIdSchema, 201)
    @require_api_access("organizer:write")
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
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventPlaceSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        pagination = get_place_query(params).paginate()
        return pagination

    @doc(
        summary="Add new place",
        tags=["Organizations", "Places"],
    )
    @use_kwargs(PlacePostRequestSchema, location="json", apply=False)
    @marshal_with(PlaceIdSchema, 201)
    @require_api_access("place:write")
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
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventReferenceSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        pagination = get_reference_incoming_query(params).paginate()
        return pagination

    @doc(
        summary="Add reference",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceCreateRequestSchema, location="json", apply=False)
    @marshal_with(EventReferenceIdSchema, 201)
    @require_api_access("eventreference:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "event:reference")

        reference = self.create_instance(
            EventReferenceCreateRequestSchema, admin_unit_id=admin_unit.id
        )
        db.session.add(reference)
        db.session.commit()

        return reference, 201


class OrganizationOutgoingEventReferenceListResource(BaseResource):
    @doc(
        summary="List outgoing event references of organization",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceListRequestSchema, location=("query"))
    @marshal_with(EventReferenceListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)

        params = EventReferenceSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        pagination = get_reference_outgoing_query(params).paginate()
        return pagination


class OrganizationIncomingEventReferenceRequestListResource(BaseResource):
    @doc(
        summary="List incoming event reference requests of organization",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestListRequestSchema, location=("query"))
    @marshal_with(EventReferenceRequestListResponseSchema)
    @require_api_access("eventreferencerequest:read")
    def get(self, id, **kwargs):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)

        params = EventReferenceRequestSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        pagination = get_reference_requests_incoming_query(params).paginate()
        return pagination


class OrganizationOutgoingEventReferenceRequestListResource(BaseResource):
    @doc(
        summary="List outgoing event reference requests of organization",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestListRequestSchema, location=("query"))
    @marshal_with(EventReferenceRequestListResponseSchema)
    @require_api_access("eventreferencerequest:read")
    def get(self, id, **kwargs):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)

        params = EventReferenceRequestSearchParams()
        params.load_from_request(**kwargs)
        params.admin_unit_id = admin_unit.id
        pagination = get_reference_requests_outgoing_query(params).paginate()
        return pagination

    @doc(
        summary="Add reference request",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestPostRequestSchema, location="json", apply=False)
    @marshal_with(EventReferenceRequestIdSchema, 201)
    @require_api_access("eventreferencerequest:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)

        reference_request = self.create_instance(EventReferenceRequestPostRequestSchema)
        event = reference_request.event

        if event.admin_unit_id != admin_unit.id:
            abort(404)

        if not can_request_event_reference(event):
            abort(401)

        db.session.add(reference_request)
        reference, _ = handle_request_according_to_relation(reference_request, event)
        db.session.commit()
        send_reference_request_mails(reference_request, reference)

        return reference_request, 201


class OrganizationOutgoingRelationListResource(BaseResource):
    @doc(
        summary="List outgoing relations of organization",
        tags=["Organizations", "Organization Relations"],
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


class OrganizationOutgoingRelationResource(BaseResource):
    @doc(
        summary="Get outgoing relation to given target organization",
        tags=["Organizations", "Organization Relations"],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_api_access("organization:read")
    def get(self, id, target_id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        relation = AdminUnitRelation.query.filter(
            AdminUnitRelation.source_admin_unit_id == id,
            AdminUnitRelation.target_admin_unit_id == target_id,
        ).first_or_404(id)
        return relation


class OrganizationOrganizationInvitationListResource(BaseResource):
    @doc(
        summary="List organization invitations of organization",
        tags=["Organizations", "Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationListRequestSchema, location=("query"))
    @marshal_with(OrganizationInvitationListResponseSchema)
    @require_api_access("organization:read")
    def get(self, id, **kwargs):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        params = TrackableSearchParams()
        params.load_from_request(**kwargs)

        query = get_admin_unit_invitation_query(admin_unit)
        query = params.get_trackable_query(query, AdminUnitInvitation)
        query = params.get_trackable_order_by(query, AdminUnitInvitation)
        return query.paginate()

    @doc(
        summary="Add new organization invitation",
        tags=["Organizations", "Organization Invitations"],
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

        send_mail_async(
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
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_event_list_query(admin_unit.id, name).paginate()
        return pagination

    @doc(
        summary="Add new event list",
        tags=["Organizations", "Event Lists"],
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
    @require_api_access()
    def get(self, id, event_id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_event_list_status_query(
            admin_unit.id, event_id, name
        ).paginate()
        return pagination


class OrganizationCustomWidgetListResource(BaseResource):
    @doc(
        summary="List custom widgets of organization",
        tags=["Organizations", "Custom Widgets"],
    )
    @use_kwargs(CustomWidgetListRequestSchema, location=("query"))
    @marshal_with(CustomWidgetListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        admin_unit = AdminUnit.query.get_or_404(id)
        name = kwargs["name"] if "name" in kwargs else None

        pagination = get_custom_widget_query(admin_unit.id, name).paginate()
        return pagination

    @doc(
        summary="Add new custom widget",
        tags=["Organizations", "CustomWidgets"],
    )
    @use_kwargs(CustomWidgetPostRequestSchema, location="json", apply=False)
    @marshal_with(CustomWidgetIdSchema, 201)
    @require_api_access("customwidget:write")
    def post(self, id):
        login_api_user_or_401()
        admin_unit = get_admin_unit_for_manage_or_404(id)
        access_or_401(admin_unit, "admin_unit:update")

        custom_widget = self.create_instance(
            CustomWidgetPostRequestSchema, admin_unit_id=admin_unit.id
        )
        db.session.add(custom_widget)
        db.session.commit()

        return custom_widget, 201


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
    OrganizationEventImportResource,
    "/organizations/<int:id>/events/import",
    "api_v1_organization_event_import",
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
    OrganizationIncomingEventReferenceRequestListResource,
    "/organizations/<int:id>/event-reference-requests/incoming",
    "api_v1_organization_incoming_event_reference_request_list",
)
add_api_resource(
    OrganizationOutgoingEventReferenceRequestListResource,
    "/organizations/<int:id>/event-reference-requests/outgoing",
    "api_v1_organization_outgoing_event_reference_request_list",
)

add_api_resource(
    OrganizationOutgoingRelationListResource,
    "/organizations/<int:id>/relations/outgoing",
    "api_v1_organization_outgoing_relation_list",
)
add_api_resource(
    OrganizationOutgoingRelationResource,
    "/organizations/<int:id>/relations/outgoing/<int:target_id>",
    "api_v1_organization_outgoing_relation",
)
add_api_resource(
    OrganizationOrganizationInvitationListResource,
    "/organizations/<int:id>/organization-invitations",
    "api_v1_organization_organization_invitation_list",
)
add_api_resource(
    OrganizationCustomWidgetListResource,
    "/organizations/<int:id>/custom-widgets",
    "api_v1_organization_custom_widget_list",
)
