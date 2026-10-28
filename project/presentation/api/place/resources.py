from flask import g, make_response, request
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import DeleteEventPlaceCommand
from project.application.queries import GetEventPlaceQuery, ResourceKind
from project.presentation.api import add_api_resource
from project.presentation.api.place.schemas import (
    PlacePatchRequestPlainSchema,
    PlacePutRequestPlainSchema,
    PlaceSchema,
)
from project.presentation.api.resources import (
    BaseResource,
    organization_item_or_404,
    require_api_access,
    require_organization_api_access,
)
from project.presentation.shared.query_results import result_or_404


def _get(resource, place_id):
    return result_or_404(resource.query_bus.handle(GetEventPlaceQuery(id=place_id)))


def _put(resource):
    cmd = PlacePutRequestPlainSchema(context=g.api_command_context).load(request.json)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _patch(resource):
    cmd = PlacePatchRequestPlainSchema(context=g.api_command_context).load(request.json)
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


def _delete(resource, place_id):
    cmd = DeleteEventPlaceCommand(
        id=place_id, actor=resource.app_context_provider.get_current_actor()
    )
    resource.message_bus.handle_command(cmd)

    return make_response("", 204)


class PlaceResource(BaseResource):
    @doc(summary="Get place", tags=["Places"])
    @marshal_with(PlaceSchema)
    @require_api_access()
    def get(self, id):
        return _get(self, id)

    @doc(
        summary="Update place",
        tags=["Places"],
    )
    @use_kwargs(PlacePutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_places:write", ResourceKind.event_place
    )
    def put(self, id):
        return _put(self)

    @doc(
        summary="Patch place",
        tags=["Places"],
    )
    @use_kwargs(PlacePatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_places:write", ResourceKind.event_place
    )
    def patch(self, id):
        return _patch(self)

    @doc(
        summary="Delete place",
        tags=["Places"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_places:write", ResourceKind.event_place
    )
    def delete(self, id):
        return _delete(self, id)


class OrganizationPlaceResource(BaseResource):
    @doc(summary="Get place of organization", tags=["Organizations", "Places"])
    @marshal_with(PlaceSchema)
    @require_api_access()
    def get(self, id, place_id):
        result = _get(self, place_id)
        organization_item_or_404(self.query_bus, ResourceKind.event_place, id, place_id)
        return result

    @doc(
        summary="Update place",
        tags=["Organizations", "Places"],
    )
    @use_kwargs(PlacePutRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_places:write", ResourceKind.event_place, item_arg="place_id"
    )
    def put(self, id, place_id):
        return _put(self)

    @doc(
        summary="Patch place",
        tags=["Organizations", "Places"],
    )
    @use_kwargs(PlacePatchRequestPlainSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_places:write", ResourceKind.event_place, item_arg="place_id"
    )
    def patch(self, id, place_id):
        return _patch(self)

    @doc(
        summary="Delete place",
        tags=["Organizations", "Places"],
    )
    @marshal_with(None, 204)
    @require_organization_api_access(
        "organization.event_places:write", ResourceKind.event_place, item_arg="place_id"
    )
    def delete(self, id, place_id):
        return _delete(self, place_id)


add_api_resource(
    PlaceResource,
    "/places/<int:id>",
    "api_v1_place",
    deprecated="/organizations/{id}/places/{place_id}",
    deprecated_methods=("put", "patch", "delete"),
)
add_api_resource(
    OrganizationPlaceResource,
    "/organizations/<int:id>/places/<int:place_id>",
    "api_v1_organization_place",
)
