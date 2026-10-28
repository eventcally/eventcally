from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import DeleteEventOrganizerCommand
from project.application.queries import GetEventOrganizerQuery, ResourceKind
from project.presentation.api import add_api_resource
from project.presentation.api.organizer.schemas import (
    OrganizerPatchRequestPlainSchema,
    OrganizerPutRequestPlainSchema,
    OrganizerSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    organization_item_or_404,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


def _get(resource, organizer_id):
    return result_or_404(
        resource.query_bus.handle(GetEventOrganizerQuery(id=organizer_id))
    )


def _put(resource):
    cmd = OrganizerPutRequestPlainSchema(context=g.api_command_context).load(
        request.json
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _patch(resource):
    cmd = OrganizerPatchRequestPlainSchema(context=g.api_command_context).load(
        request.json
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _delete(resource, organizer_id):
    cmd = DeleteEventOrganizerCommand(
        id=organizer_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


class OrganizerResource(BaseResource):
    @doc(summary="Get organizer", tags=["Organizers"])
    @marshal_with(OrganizerSchema)
    @require_api_access()
    def get(self, id):
        return _get(self, id)

    @doc(
        summary="Update organizer",
        tags=["Organizers"],
    )
    @use_kwargs(OrganizerPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", ResourceKind.event_organizer
    )
    def put(self, id):
        return _put(self)

    @doc(
        summary="Patch organizer",
        tags=["Organizers"],
    )
    @use_kwargs(OrganizerPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", ResourceKind.event_organizer
    )
    def patch(self, id):
        return _patch(self)

    @doc(
        summary="Delete organizer",
        tags=["Organizers"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write", ResourceKind.event_organizer
    )
    def delete(self, id):
        return _delete(self, id)


class OrganizationOrganizerResource(BaseResource):
    @doc(summary="Get organizer of organization", tags=["Organizations", "Organizers"])
    @marshal_with(OrganizerSchema)
    @require_api_access()
    def get(self, id, organizer_id):
        result = _get(self, organizer_id)
        organization_item_or_404(
            self.query_bus, ResourceKind.event_organizer, id, organizer_id
        )
        return result

    @doc(
        summary="Update organizer",
        tags=["Organizations", "Organizers"],
    )
    @use_kwargs(OrganizerPutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write",
        ResourceKind.event_organizer,
        item_arg="organizer_id",
    )
    def put(self, id, organizer_id):
        return _put(self)

    @doc(
        summary="Patch organizer",
        tags=["Organizations", "Organizers"],
    )
    @use_kwargs(OrganizerPatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write",
        ResourceKind.event_organizer,
        item_arg="organizer_id",
    )
    def patch(self, id, organizer_id):
        return _patch(self)

    @doc(
        summary="Delete organizer",
        tags=["Organizations", "Organizers"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_organizers:write",
        ResourceKind.event_organizer,
        item_arg="organizer_id",
    )
    def delete(self, id, organizer_id):
        return _delete(self, organizer_id)


add_api_resource(
    OrganizerResource,
    "/organizers/<int:id>",
    "api_v1_organizer",
    deprecated="/organizations/{id}/organizers/{organizer_id}",
    deprecated_methods=("put", "patch", "delete"),
)
add_api_resource(
    OrganizationOrganizerResource,
    "/organizations/<int:id>/organizers/<int:organizer_id>",
    "api_v1_organization_organizer",
)
