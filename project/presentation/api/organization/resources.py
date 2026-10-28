from flask import abort, g, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import RequestEventReferenceCommand
from project.application.queries import (
    CanRequestVerificationQuery,
    GetEventDetailQuery,
    GetOrganizationQuery,
    GetOutgoingOrganizationRelationByTargetQuery,
    ListEventOrganizersQuery,
    ListEventPlacesQuery,
    ListEventsQuery,
    ListIncomingEventReferenceRequestsQuery,
    ListIncomingEventReferencesQuery,
    ListIncomingOrganizationVerificationRequestsQuery,
    ListOrganizationInvitationsQuery,
    ListOutgoingEventReferenceRequestsQuery,
    ListOutgoingEventReferencesQuery,
    ListOutgoingOrganizationRelationsQuery,
    ListOutgoingOrganizationVerificationRequestsQuery,
    OrganizationInvitationSort,
    SearchEventDatesQuery,
    SearchEventsQuery,
    SearchOrganizationsQuery,
    TrackableSort,
)
from project.domain.errors import UnauthorizedError
from project.presentation.api import add_api_resource
from project.presentation.api.event.schemas import (
    EventCreateRequestPlainSchema,
    EventIdPlainSchema,
    EventListRequestSchema,
    EventListResponseSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.presentation.api.event_date.schemas import (
    EventDateSearchRequestSchema,
    EventDateSearchResponseSchema,
)
from project.presentation.api.event_reference.schemas import (
    EventReferenceCreateRequestPlainSchema,
    EventReferenceIdPlainSchema,
    EventReferenceListRequestSchema,
    EventReferenceListResponseSchema,
)
from project.presentation.api.event_reference_request.schemas import (
    EventReferenceRequestCreateRequestPlainSchema,
    EventReferenceRequestIdSchema,
    EventReferenceRequestListRequestSchema,
    EventReferenceRequestListResponseSchema,
    EventReferenceRequestPostRequestSchema,
)
from project.presentation.api.organization.schemas import (
    OrganizationListRequestSchema,
    OrganizationListResponseSchema,
    OrganizationSchema,
)
from project.presentation.api.organization_invitation.schemas import (
    OrganizationInvitationCreateRequestPlainSchema,
    OrganizationInvitationCreateRequestSchema,
    OrganizationInvitationIdPlainSchema,
    OrganizationInvitationListRequestSchema,
    OrganizationInvitationListResponseSchema,
)
from project.presentation.api.organization_relation.schemas import (
    OrganizationRelationCreateRequestPlainSchema,
    OrganizationRelationCreateRequestSchema,
    OrganizationRelationIdPlainSchema,
    OrganizationRelationListRequestSchema,
    OrganizationRelationListResponseSchema,
    OrganizationRelationSchema,
)
from project.presentation.api.organization_verification_request.schemas import (
    OrganizationVerificationRequestCreateRequestPlainSchema,
    OrganizationVerificationRequestIdPlainSchema,
    OrganizationVerificationRequestListRequestSchema,
    OrganizationVerificationRequestListResponseSchema,
    OrganizationVerificationRequestPostRequestSchema,
)
from project.presentation.api.organizer.schemas import (
    OrganizerCreateRequestPlainSchema,
    OrganizerIdPlainSchema,
    OrganizerListRequestSchema,
    OrganizerListResponseSchema,
)
from project.presentation.api.place.schemas import (
    PlaceCreateRequestPlainSchema,
    PlaceIdPlainSchema,
    PlaceListRequestSchema,
    PlaceListResponseSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.access import (
    can_request_event_reference,
    can_verify_admin_unit,
    login_api_user,
)
from project.presentation.shared.current_admin_unit import (
    get_current_admin_unit_for_api,
)
from project.presentation.shared.event_query_args import (
    event_search_criteria_from_request,
    reference_admin_unit_id_for_api,
)
from project.presentation.shared.query_args import (
    enum_or_none,
    list_arg_from_request,
    page_request_from_kwargs,
    trackable_criteria_from_kwargs,
    trackable_sort_from_kwargs,
)
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)


class OrganizationResource(BaseResource):
    @doc(summary="Get organization", tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    @require_api_access()
    def get(self, id):
        return result_or_404(self.query_bus.handle(GetOrganizationQuery(id=id)))


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
        result_or_404(self.query_bus.handle(GetOrganizationQuery(id=id)))
        login_api_user()

        page = self.query_bus.handle(
            SearchEventDatesQuery(
                criteria=event_search_criteria_from_request(
                    kwargs,
                    defaults=dict(include_admin_unit_references=True),
                    admin_unit_id=id,
                    include_private=True,
                ),
                reference_admin_unit_id=reference_admin_unit_id_for_api(),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class OrganizationEventSearchResource(BaseResource):
    @doc(summary="Search for events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        result_or_404(self.query_bus.handle(GetOrganizationQuery(id=id)))
        login_api_user()

        page = self.query_bus.handle(
            SearchEventsQuery(
                criteria=event_search_criteria_from_request(
                    kwargs, admin_unit_id=id, include_private=True
                ),
                reference_admin_unit_id=reference_admin_unit_id_for_api(),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class OrganizationEventListResource(BaseResource):

    @doc(summary="List events of organization", tags=["Organizations", "Events"])
    @use_kwargs(EventListRequestSchema, location=("query"))
    @marshal_with(EventListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        login_api_user()
        page = result_or_404(
            self.query_bus.handle(
                ListEventsQuery(
                    admin_unit_id=id,
                    include_private=True,
                    trackable=trackable_criteria_from_kwargs(kwargs),
                    sort=enum_or_none(TrackableSort, kwargs.get("sort")),
                    page=page_request_from_kwargs(kwargs),
                )
            )
        )
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add new event",
        tags=["Organizations", "Events"],
    )
    @use_kwargs(EventCreateRequestPlainSchema, location="json", apply=False)
    @marshal_with(EventIdPlainSchema, 201)
    @require_organization_api_access("organization.events:write")
    def post(self, id):
        cmd = EventCreateRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        cmd_result = self.message_bus.handle_command(cmd)
        return cmd_result, 201


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

        page = self.query_bus.handle(
            SearchOrganizationsQuery(
                keyword=kwargs.get("keyword") or None,
                postal_codes=list_arg_from_request("postal_code"),
                include_unverified=include_unverified,
                reference_request_for_admin_unit_id=reference_request_for_admin_unit_id,
                trackable=trackable_criteria_from_kwargs(kwargs),
                sort=enum_or_none(TrackableSort, kwargs.get("sort")),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


class OrganizationOrganizerListResource(BaseResource):
    @doc(
        summary="List organizers of organization", tags=["Organizations", "Organizers"]
    )
    @use_kwargs(OrganizerListRequestSchema, location=("query"))
    @marshal_with(OrganizerListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        query = ListEventOrganizersQuery(
            admin_unit_id=id,
            name=kwargs.get("name"),
            sort=kwargs.get("sort"),
            trackable=trackable_criteria_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add new organizer",
        tags=["Organizations", "Organizers"],
    )
    @use_kwargs(OrganizerCreateRequestPlainSchema, location="json", apply=False)
    @marshal_with(OrganizerIdPlainSchema, 201)
    @require_organization_api_access("organization.event_organizers:write")
    def post(self, id):
        cmd = OrganizerCreateRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        cmd_result = self.message_bus.handle_command(cmd)
        return cmd_result, 201


class OrganizationPlaceListResource(BaseResource):
    @doc(summary="List places of organization", tags=["Organizations", "Places"])
    @use_kwargs(PlaceListRequestSchema, location=("query"))
    @marshal_with(PlaceListResponseSchema)
    @require_api_access()
    def get(self, id, **kwargs):
        query = ListEventPlacesQuery(
            admin_unit_id=id,
            name=kwargs.get("name"),
            sort=kwargs.get("sort"),
            trackable=trackable_criteria_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add new place",
        tags=["Organizations", "Places"],
    )
    @use_kwargs(PlaceCreateRequestPlainSchema, location="json", apply=False)
    @marshal_with(PlaceIdPlainSchema, 201)
    @require_organization_api_access("organization.event_places:write")
    def post(self, id):
        cmd = PlaceCreateRequestPlainSchema(context=g.api_command_context).load(
            request.json
        )
        cmd_result = self.message_bus.handle_command(cmd)
        return cmd_result, 201


class OrganizationIncomingEventReferenceListResource(BaseResource):
    @doc(
        summary="List incoming event references of organization",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceListRequestSchema, location=("query"))
    @marshal_with(EventReferenceListResponseSchema)
    @require_organization_api_access("organization.incoming_event_references:read")
    def get(self, id, **kwargs):
        query = ListIncomingEventReferencesQuery(
            admin_unit_id=id,
            trackable=trackable_criteria_from_kwargs(kwargs),
            sort=trackable_sort_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add reference",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceCreateRequestPlainSchema, location="json", apply=False)
    @marshal_with(EventReferenceIdPlainSchema, 201)
    @require_organization_api_access("organization.incoming_event_references:write")
    def post(self, id):
        cmd = EventReferenceCreateRequestPlainSchema(
            context=g.api_command_context
        ).load(request.json)
        cmd_result = self.message_bus.handle_command(cmd)
        return cmd_result, 201


class OrganizationOutgoingEventReferenceListResource(BaseResource):
    @doc(
        summary="List outgoing event references of organization",
        tags=["Organizations", "Event References"],
    )
    @use_kwargs(EventReferenceListRequestSchema, location=("query"))
    @marshal_with(EventReferenceListResponseSchema)
    @require_organization_api_access("organization.outgoing_event_references:read")
    def get(self, id, **kwargs):
        query = ListOutgoingEventReferencesQuery(
            admin_unit_id=id,
            trackable=trackable_criteria_from_kwargs(kwargs),
            sort=trackable_sort_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page


def _list_incoming_event_reference_requests(resource, id, kwargs):
    query = ListIncomingEventReferenceRequestsQuery(
        admin_unit_id=id,
        trackable=trackable_criteria_from_kwargs(kwargs),
        sort=trackable_sort_from_kwargs(kwargs),
        page=page_request_from_kwargs(kwargs),
    )
    page = result_or_404(resource.query_bus.handle(query))
    abort_if_page_out_of_range(page)
    return page


class OrganizationIncomingEventReferenceRequestListResource(BaseResource):
    @doc(
        summary="List incoming event reference requests of organization",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestListRequestSchema, location=("query"))
    @marshal_with(EventReferenceRequestListResponseSchema)
    @require_organization_api_access("organization.incoming_event_references:read")
    def get(self, id, **kwargs):
        return _list_incoming_event_reference_requests(self, id, kwargs)


class OrganizationIncomingEventReferenceRequestsResource(BaseResource):
    """The list under the organization-scoped URL; it requires the scope the
    handler checks (the deprecated list requires the references scope)."""

    @doc(
        summary="List incoming event reference requests of organization",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestListRequestSchema, location=("query"))
    @marshal_with(EventReferenceRequestListResponseSchema)
    @require_organization_api_access(
        "organization.incoming_event_reference_requests:read"
    )
    def get(self, id, **kwargs):
        return _list_incoming_event_reference_requests(self, id, kwargs)


class OrganizationOutgoingEventReferenceRequestListResource(BaseResource):
    @doc(
        summary="List outgoing event reference requests of organization",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestListRequestSchema, location=("query"))
    @marshal_with(EventReferenceRequestListResponseSchema)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:read"
    )
    def get(self, id, **kwargs):
        query = ListOutgoingEventReferenceRequestsQuery(
            admin_unit_id=id,
            trackable=trackable_criteria_from_kwargs(kwargs),
            sort=trackable_sort_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add reference request",
        tags=["Organizations", "Event Reference Requests"],
    )
    @use_kwargs(EventReferenceRequestPostRequestSchema, location="json", apply=False)
    @marshal_with(EventReferenceRequestIdSchema, 201)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:write"
    )
    def post(self, id):
        admin_unit = g.manage_admin_unit

        data = self.load_command(EventReferenceRequestCreateRequestPlainSchema)
        try:
            event = result_or_404(
                self.query_bus.handle(GetEventDetailQuery(id=data["event_id"]))
            )
        except UnauthorizedError:
            abort(404)

        if event.admin_unit_id != admin_unit.id:
            abort(404)

        if not can_request_event_reference(event):
            abort(401)

        cmd = RequestEventReferenceCommand(
            actor=self.app_context_provider.get_current_actor(),
            admin_unit_id=data["admin_unit_id"],
            event_id=event.id,
        )
        cmd_result = self.message_bus.handle_command(cmd)

        return {"id": cmd_result.id}, 201


def _list_incoming_verification_requests(resource, id, kwargs):
    query = ListIncomingOrganizationVerificationRequestsQuery(
        admin_unit_id=id,
        trackable=trackable_criteria_from_kwargs(kwargs),
        sort=trackable_sort_from_kwargs(kwargs),
        page=page_request_from_kwargs(kwargs),
    )
    page = result_or_404(resource.query_bus.handle(query))
    abort_if_page_out_of_range(page)
    return page


def _list_outgoing_verification_requests(resource, id, kwargs):
    query = ListOutgoingOrganizationVerificationRequestsQuery(
        admin_unit_id=id,
        trackable=trackable_criteria_from_kwargs(kwargs),
        sort=trackable_sort_from_kwargs(kwargs),
        page=page_request_from_kwargs(kwargs),
    )
    page = result_or_404(resource.query_bus.handle(query))
    abort_if_page_out_of_range(page)
    return page


class OrganizationIncomingOrganizationVerificationRequestListResource(BaseResource):
    @doc(
        summary="List incoming organization verification requests of organization",
        tags=["Organizations", "Organization Verification Requests"],
    )
    @use_kwargs(OrganizationVerificationRequestListRequestSchema, location=("query"))
    @marshal_with(OrganizationVerificationRequestListResponseSchema)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:read"
    )
    def get(self, id, **kwargs):
        return _list_incoming_verification_requests(self, id, kwargs)


class OrganizationIncomingOrganizationVerificationRequestsResource(BaseResource):
    """The list under the organization-scoped URL; it requires the scope the
    handler checks (the deprecated list requires a reference request scope)."""

    @doc(
        summary="List incoming organization verification requests of organization",
        tags=["Organizations", "Organization Verification Requests"],
    )
    @use_kwargs(OrganizationVerificationRequestListRequestSchema, location=("query"))
    @marshal_with(OrganizationVerificationRequestListResponseSchema)
    @require_organization_api_access(
        "organization.incoming_organization_verification_requests:read"
    )
    def get(self, id, **kwargs):
        return _list_incoming_verification_requests(self, id, kwargs)


class OrganizationOutgoingOrganizationVerificationRequestListResource(BaseResource):
    @doc(
        summary="List outgoing organization verification requests of organization",
        tags=["Organizations", "Organization Verification Requests"],
    )
    @use_kwargs(OrganizationVerificationRequestListRequestSchema, location=("query"))
    @marshal_with(OrganizationVerificationRequestListResponseSchema)
    @require_organization_api_access(
        "organization.outgoing_event_reference_requests:read"
    )
    def get(self, id, **kwargs):
        return _list_outgoing_verification_requests(self, id, kwargs)

    @doc(
        summary="Add verification request",
        tags=["Organizations", "Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestPostRequestSchema, location="json", apply=False
    )
    @marshal_with(OrganizationVerificationRequestIdPlainSchema, 201)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:write"
    )
    def post(self, id):
        return _post_verification_request(self)


class OrganizationOutgoingOrganizationVerificationRequestsResource(BaseResource):
    """The resource under the organization-scoped URL; its list requires the scope
    the handler checks (the deprecated list requires a reference request scope)."""

    @doc(
        summary="List outgoing organization verification requests of organization",
        tags=["Organizations", "Organization Verification Requests"],
    )
    @use_kwargs(OrganizationVerificationRequestListRequestSchema, location=("query"))
    @marshal_with(OrganizationVerificationRequestListResponseSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:read"
    )
    def get(self, id, **kwargs):
        return _list_outgoing_verification_requests(self, id, kwargs)

    @doc(
        summary="Add verification request",
        tags=["Organizations", "Organization Verification Requests"],
    )
    @use_kwargs(
        OrganizationVerificationRequestPostRequestSchema, location="json", apply=False
    )
    @marshal_with(OrganizationVerificationRequestIdPlainSchema, 201)
    @require_organization_api_access(
        "organization.outgoing_organization_verification_requests:write"
    )
    def post(self, id):
        return _post_verification_request(self)


def _post_verification_request(resource):
    admin_unit = g.manage_admin_unit
    cmd = resource.load_command(OrganizationVerificationRequestCreateRequestPlainSchema)
    result_or_404(
        resource.query_bus.handle(GetOrganizationQuery(id=cmd.target_admin_unit_id))
    )

    if not resource.query_bus.handle(
        CanRequestVerificationQuery(
            source_admin_unit_id=admin_unit.id,
            target_admin_unit_id=cmd.target_admin_unit_id,
        )
    ):
        abort(401)

    cmd_result = resource.message_bus.handle_command(cmd)

    return cmd_result, 201


class OrganizationOutgoingRelationListResource(BaseResource):
    @doc(
        summary="List outgoing relations of organization",
        tags=["Organizations", "Organization Relations"],
    )
    @use_kwargs(OrganizationRelationListRequestSchema, location=("query"))
    @marshal_with(OrganizationRelationListResponseSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:read"
    )
    def get(self, id, **kwargs):
        query = ListOutgoingOrganizationRelationsQuery(
            admin_unit_id=id, page=page_request_from_kwargs(kwargs)
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add new outgoing relation",
        tags=["Organizations", "Organization Relations"],
    )
    @use_kwargs(OrganizationRelationCreateRequestSchema, location="json", apply=False)
    @marshal_with(OrganizationRelationIdPlainSchema, 201)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:write"
    )
    def post(self, id):
        cmd = self.load_command(OrganizationRelationCreateRequestPlainSchema)
        cmd_result = self.message_bus.handle_command(cmd)

        return cmd_result, 201


class OrganizationOutgoingRelationResource(BaseResource):
    @doc(
        summary="Get outgoing relation to given target organization",
        tags=["Organizations", "Organization Relations"],
    )
    @marshal_with(OrganizationRelationSchema)
    @require_organization_api_access(
        "organization.outgoing_organization_relations:read"
    )
    def get(self, id, target_id):
        return result_or_404(
            self.query_bus.handle(
                GetOutgoingOrganizationRelationByTargetQuery(
                    admin_unit_id=id, target_admin_unit_id=target_id
                )
            )
        )


def _invitation_sort_or_none(value):
    """The schema accepts `name`, but invitations have no name; the ORM path
    ignored it, so it falls back to the default order."""
    try:
        return OrganizationInvitationSort(value)
    except ValueError:
        return None


class OrganizationOrganizationInvitationListResource(BaseResource):
    @doc(
        summary="List organization invitations of organization",
        tags=["Organizations", "Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationListRequestSchema, location=("query"))
    @marshal_with(OrganizationInvitationListResponseSchema)
    @require_organization_api_access("organization.organization_invitations:read")
    def get(self, id, **kwargs):
        query = ListOrganizationInvitationsQuery(
            admin_unit_id=id,
            sort=_invitation_sort_or_none(kwargs.get("sort")),
            trackable=trackable_criteria_from_kwargs(kwargs),
            page=page_request_from_kwargs(kwargs),
        )
        page = result_or_404(self.query_bus.handle(query))
        abort_if_page_out_of_range(page)
        return page

    @doc(
        summary="Add new organization invitation",
        tags=["Organizations", "Organization Invitations"],
    )
    @use_kwargs(OrganizationInvitationCreateRequestSchema, location="json", apply=False)
    @marshal_with(OrganizationInvitationIdPlainSchema, 201)
    @require_organization_api_access("organization.organization_invitations:write")
    def post(self, id):
        cmd = self.load_command(OrganizationInvitationCreateRequestPlainSchema)
        cmd_result = self.message_bus.handle_command(cmd)

        return cmd_result, 201


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
_ORG = "/organizations/<int:id>"
_ORG_DOC = "/organizations/{id}"
_BY_TARGET = "outgoing-organization-relations/by-target/<int:target_id>"

# Organization-scoped routes (the shape of the web routes) ...
add_api_resource(
    OrganizationIncomingEventReferenceListResource,
    f"{_ORG}/incoming-event-references",
    "api_v1_organization_incoming_event_references",
)
add_api_resource(
    OrganizationOutgoingEventReferenceListResource,
    f"{_ORG}/outgoing-event-references",
    "api_v1_organization_outgoing_event_references",
)
add_api_resource(
    OrganizationIncomingEventReferenceRequestsResource,
    f"{_ORG}/incoming-event-reference-requests",
    "api_v1_organization_incoming_event_reference_requests",
)
add_api_resource(
    OrganizationOutgoingEventReferenceRequestListResource,
    f"{_ORG}/outgoing-event-reference-requests",
    "api_v1_organization_outgoing_event_reference_requests",
)
add_api_resource(
    OrganizationIncomingOrganizationVerificationRequestsResource,
    f"{_ORG}/incoming-organization-verification-requests",
    "api_v1_organization_incoming_organization_verification_requests",
)
add_api_resource(
    OrganizationOutgoingOrganizationVerificationRequestsResource,
    f"{_ORG}/outgoing-organization-verification-requests",
    "api_v1_organization_outgoing_organization_verification_requests",
)
add_api_resource(
    OrganizationOutgoingRelationListResource,
    f"{_ORG}/outgoing-organization-relations",
    "api_v1_organization_outgoing_organization_relations",
)
add_api_resource(
    OrganizationOutgoingRelationResource,
    f"{_ORG}/{_BY_TARGET}",
    "api_v1_organization_outgoing_organization_relation_by_target",
)

# ... and the deprecated routes they replace.
add_api_resource(
    OrganizationIncomingEventReferenceListResource,
    f"{_ORG}/event-references/incoming",
    "api_v1_organization_incoming_event_reference_list",
    deprecated=f"{_ORG_DOC}/incoming-event-references",
)
add_api_resource(
    OrganizationOutgoingEventReferenceListResource,
    f"{_ORG}/event-references/outgoing",
    "api_v1_organization_outgoing_event_reference_list",
    deprecated=f"{_ORG_DOC}/outgoing-event-references",
)
add_api_resource(
    OrganizationIncomingEventReferenceRequestListResource,
    f"{_ORG}/event-reference-requests/incoming",
    "api_v1_organization_incoming_event_reference_request_list",
    deprecated=f"{_ORG_DOC}/incoming-event-reference-requests",
)
add_api_resource(
    OrganizationOutgoingEventReferenceRequestListResource,
    f"{_ORG}/event-reference-requests/outgoing",
    "api_v1_organization_outgoing_event_reference_request_list",
    deprecated=f"{_ORG_DOC}/outgoing-event-reference-requests",
)
add_api_resource(
    OrganizationIncomingOrganizationVerificationRequestListResource,
    f"{_ORG}/organization-verification-requests/incoming",
    "api_v1_organization_incoming_organization_verification_request_list",
    deprecated=f"{_ORG_DOC}/incoming-organization-verification-requests",
)
add_api_resource(
    OrganizationOutgoingOrganizationVerificationRequestListResource,
    f"{_ORG}/organization-verification-requests/outgoing",
    "api_v1_organization_outgoing_organization_verification_request_list",
    deprecated=f"{_ORG_DOC}/outgoing-organization-verification-requests",
)
add_api_resource(
    OrganizationOutgoingRelationListResource,
    f"{_ORG}/relations/outgoing",
    "api_v1_organization_outgoing_relation_list",
    deprecated=f"{_ORG_DOC}/outgoing-organization-relations",
)
add_api_resource(
    OrganizationOutgoingRelationResource,
    f"{_ORG}/relations/outgoing/<int:target_id>",
    "api_v1_organization_outgoing_relation",
    deprecated=f"{_ORG_DOC}/outgoing-organization-relations/by-target/{{target_id}}",
)
add_api_resource(
    OrganizationOrganizationInvitationListResource,
    "/organizations/<int:id>/organization-invitations",
    "api_v1_organization_organization_invitation_list",
)
