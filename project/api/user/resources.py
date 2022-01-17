from flask import abort
from flask.helpers import make_response
from flask_apispec import doc, marshal_with, use_kwargs
from flask_security import current_user

from project import db
from project.access import login_api_user_or_401
from project.api import add_api_resource
from project.api.event.schemas import (
    EventSearchRequestSchema,
    EventSearchResponseSchema,
    UserFavoriteEventListRequestSchema,
    UserFavoriteEventListResponseSchema,
)
from project.api.organization_invitation.schemas import (
    OrganizationInvitationListRequestSchema,
    OrganizationInvitationListResponseSchema,
    OrganizationInvitationSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import AdminUnitInvitation, Event
from project.services.admin_unit import get_admin_unit_organization_invitations_query
from project.services.event import get_events_query
from project.services.event_search import EventSearchParams
from project.utils import strings_are_equal_ignoring_case


def invitation_receiver_or_401(invitation: AdminUnitInvitation):
    if not strings_are_equal_ignoring_case(invitation.email, current_user.email):
        abort(401)


class UserOrganizationInvitationListResource(BaseResource):
    @doc(
        summary="List organization invitations of user",
        tags=["Users", "Organization Invitations"],
        security=[{"oauth2": ["user:read"]}],
    )
    @use_kwargs(OrganizationInvitationListRequestSchema, location=("query"))
    @marshal_with(OrganizationInvitationListResponseSchema)
    @require_api_access("user:read")
    def get(self, **kwargs):
        login_api_user_or_401()

        pagination = get_admin_unit_organization_invitations_query(
            current_user.email
        ).paginate()

        return pagination


class UserOrganizationInvitationResource(BaseResource):
    @doc(
        summary="Get organization invitation of user",
        tags=["Users", "Organization Invitations"],
        security=[{"oauth2": ["user:read"]}],
    )
    @marshal_with(OrganizationInvitationSchema)
    @require_api_access("user:read")
    def get(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        invitation_receiver_or_401(invitation)

        return invitation

    @doc(
        summary="Delete organization invitation of user",
        tags=["Users", "Organization Invitations"],
        security=[{"oauth2": ["user:write"]}],
    )
    @marshal_with(None, 204)
    @require_api_access("user:write")
    def delete(self, id):
        login_api_user_or_401()
        invitation = AdminUnitInvitation.query.get_or_404(id)
        invitation_receiver_or_401(invitation)

        db.session.delete(invitation)
        db.session.commit()

        return make_response("", 204)


class UserFavoriteEventListResource(BaseResource):
    @doc(
        summary="List favorite events of user",
        tags=["Users", "Events"],
        security=[{"oauth2": ["user:read"]}],
    )
    @use_kwargs(UserFavoriteEventListRequestSchema, location=("query"))
    @marshal_with(UserFavoriteEventListResponseSchema)
    @require_api_access("user:read")
    def get(self, **kwargs):
        from project.services.user import get_favorite_events_query

        login_api_user_or_401()

        pagination = get_favorite_events_query(current_user.id).paginate()
        return pagination


class UserFavoriteEventSearchResource(BaseResource):
    @doc(
        summary="Search for favorite events of user",
        tags=["Users", "Events"],
        security=[{"oauth2": ["user:read"]}],
    )
    @use_kwargs(EventSearchRequestSchema, location=("query"))
    @marshal_with(EventSearchResponseSchema)
    @require_api_access("user:read")
    def get(self, **kwargs):
        login_api_user_or_401()

        params = EventSearchParams()
        params.load_from_request()
        params.favored_by_user_id = current_user.id

        pagination = get_events_query(params).paginate()
        return pagination


class UserFavoriteEventListWriteResource(BaseResource):
    @doc(
        summary="Add event to users favorites",
        tags=["Users", "Events"],
        security=[{"oauth2": ["user:write"]}],
    )
    @marshal_with(None, 204)
    @require_api_access("user:write")
    def put(self, event_id):
        from project.services.user import add_favorite_event

        login_api_user_or_401()
        event = Event.query.get_or_404(event_id)

        if add_favorite_event(current_user.id, event.id):
            db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Remove event from users favorites",
        tags=["Users", "Events"],
        security=[{"oauth2": ["user:write"]}],
    )
    @marshal_with(None, 204)
    @require_api_access("user:write")
    def delete(self, event_id):
        from project.services.user import remove_favorite_event

        login_api_user_or_401()
        event = Event.query.get_or_404(event_id)

        if remove_favorite_event(current_user.id, event.id):
            db.session.commit()

        return make_response("", 204)


add_api_resource(
    UserOrganizationInvitationListResource,
    "/user/organization-invitations",
    "api_v1_user_organization_invitation_list",
)

add_api_resource(
    UserOrganizationInvitationResource,
    "/user/organization-invitation/<int:id>",
    "api_v1_user_organization_invitation",
)

add_api_resource(
    UserFavoriteEventListResource,
    "/user/favorite-events",
    "api_v1_user_favorite_event_list",
)

add_api_resource(
    UserFavoriteEventSearchResource,
    "/user/favorite-events/search",
    "api_v1_user_favorite_event_search",
)

add_api_resource(
    UserFavoriteEventListWriteResource,
    "/user/favorite-events/<int:event_id>",
    "api_v1_user_favorite_event_list_write",
)
