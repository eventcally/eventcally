from project.api import add_api_resource
from flask import make_response
from flask_apispec import marshal_with, doc, use_kwargs
from project.api.resources import BaseResource
from project.api.organizer.schemas import (
    OrganizerSchema,
    OrganizerPostRequestSchema,
    OrganizerPatchRequestSchema,
)
from project.models import EventOrganizer
from project.oauth2 import require_oauth
from authlib.integrations.flask_oauth2 import current_token
from project import db
from project.access import access_or_401, login_api_user_or_401


class OrganizerResource(BaseResource):
    @doc(summary="Get organizer", tags=["Organizers"])
    @marshal_with(OrganizerSchema)
    def get(self, id):
        return EventOrganizer.query.get_or_404(id)

    @doc(
        summary="Update organizer",
        tags=["Organizers"],
        security=[{"oauth2": ["organizer:write"]}],
    )
    @use_kwargs(OrganizerPostRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_oauth("organizer:write")
    def put(self, id):
        login_api_user_or_401(current_token.user)
        organizer = EventOrganizer.query.get_or_404(id)
        access_or_401(organizer.adminunit, "organizer:update")

        organizer = self.update_instance(OrganizerPostRequestSchema, instance=organizer)
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Patch organizer",
        tags=["Organizers"],
        security=[{"oauth2": ["organizer:write"]}],
    )
    @use_kwargs(OrganizerPatchRequestSchema, location="json", apply=False)
    @marshal_with(None, 204)
    @require_oauth("organizer:write")
    def patch(self, id):
        login_api_user_or_401(current_token.user)
        organizer = EventOrganizer.query.get_or_404(id)
        access_or_401(organizer.adminunit, "organizer:update")

        organizer = self.update_instance(
            OrganizerPatchRequestSchema, instance=organizer
        )
        db.session.commit()

        return make_response("", 204)

    @doc(
        summary="Delete organizer",
        tags=["Organizers"],
        security=[{"oauth2": ["organizer:write"]}],
    )
    @marshal_with(None, 204)
    @require_oauth("organizer:write")
    def delete(self, id):
        login_api_user_or_401(current_token.user)
        organizer = EventOrganizer.query.get_or_404(id)
        access_or_401(organizer.adminunit, "organizer:delete")

        db.session.delete(organizer)
        db.session.commit()

        return make_response("", 204)


add_api_resource(
    OrganizerResource,
    "/organizers/<int:id>",
    "api_v1_organizer",
)
