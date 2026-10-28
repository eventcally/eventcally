from flask import abort, g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands.delete_event_command import DeleteEventCommand
from project.application.queries import (
    GetEventDetailQuery,
    ResourceKind,
    SearchEventsQuery,
)
from project.presentation.api import add_api_resource
from project.presentation.api.event.schemas import (
    EventPatchRequestPlainSchema,
    EventPutRequestPlainSchema,
    EventSchema,
    EventSearchRequestSchema,
    EventSearchResponseSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.access import login_api_user
from project.presentation.shared.event_query_args import (
    event_search_criteria_from_request,
    reference_admin_unit_id_for_api,
)
from project.presentation.shared.query_args import page_request_from_kwargs
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)


def _get_detail(resource, event_id):
    login_api_user()
    return result_or_404(
        resource.query_bus.handle(
            GetEventDetailQuery(
                id=event_id, reference_admin_unit_id=reference_admin_unit_id_for_api()
            )
        )
    )


def _put(resource):
    cmd = EventPutRequestPlainSchema(context=g.api_command_context).load(request.json)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _patch(resource):
    cmd = EventPatchRequestPlainSchema(context=g.api_command_context).load(request.json)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _delete(resource, event_id):
    cmd = DeleteEventCommand(
        id=event_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


class EventResource(BaseResource):

    @doc(summary="Get event", tags=["Events"])
    @marshal_with(EventSchema)
    @require_api_access()
    def get(self, id):
        return _get_detail(self, id)

    @doc(
        summary="Update event",
        tags=["Events"],
    )
    @use_kwargs(EventPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", ResourceKind.event)
    def put(self, id):
        return _put(self)

    @doc(
        summary="Patch event",
        tags=["Events"],
    )
    @use_kwargs(EventPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", ResourceKind.event)
    def patch(self, id):
        return _patch(self)

    @doc(
        summary="Delete event",
        tags=["Events"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access("organization.events:write", ResourceKind.event)
    def delete(self, id):
        return _delete(self, id)


class OrganizationEventResource(BaseResource):
    @doc(summary="Get event of organization", tags=["Organizations", "Events"])
    @marshal_with(EventSchema)
    @require_api_access()
    def get(self, id, event_id):
        # Readability first (401), ownership second (404): the other order would
        # reveal the owner of a non-public event through the status code.
        detail = _get_detail(self, event_id)

        if detail.admin_unit.id != id:
            abort(404)

        return detail

    @doc(
        summary="Update event",
        tags=["Organizations", "Events"],
    )
    @use_kwargs(EventPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.events:write", ResourceKind.event, item_arg="event_id"
    )
    def put(self, id, event_id):
        return _put(self)

    @doc(
        summary="Patch event",
        tags=["Organizations", "Events"],
    )
    @use_kwargs(EventPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.events:write", ResourceKind.event, item_arg="event_id"
    )
    def patch(self, id, event_id):
        return _patch(self)

    @doc(
        summary="Delete event",
        tags=["Organizations", "Events"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.events:write", ResourceKind.event, item_arg="event_id"
    )
    def delete(self, id, event_id):
        return _delete(self, event_id)


class EventSearchResource(BaseResource):
    @doc(summary="Search for events", tags=["Events"])
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access()
    def get(self, **kwargs):
        login_api_user()
        page = self.query_bus.handle(
            SearchEventsQuery(
                criteria=event_search_criteria_from_request(kwargs),
                reference_admin_unit_id=reference_admin_unit_id_for_api(),
                page=page_request_from_kwargs(kwargs),
            )
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(
    EventResource,
    "/events/<int:id>",
    "api_v1_event",
    deprecated="/organizations/{id}/events/{event_id}",
    deprecated_methods=("put", "patch", "delete"),
)
add_api_resource(
    OrganizationEventResource,
    "/organizations/<int:id>/events/<int:event_id>",
    "api_v1_organization_event",
)
add_api_resource(EventSearchResource, "/events/search", "api_v1_event_search")
