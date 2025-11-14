from typing import Annotated

from dependency_injector.wiring import Provide
from flask import abort, g, url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup

from project.access import can_request_event_reference
from project.models.event import Event
from project.modular.base_views import BaseCreateView, BaseListView
from project.services import organization_service
from project.views.manage_admin_unit.outgoing_event_reference_request.forms import (
    CreateForm,
)
from project.views.reference_request import get_success_text_for_request_creation


class ListView(BaseListView):
    def get_instruction(self, **kwargs):
        request_open = "&quot;"
        request_close = "&quot;"
        request_title = gettext("Request reference")

        search_open = '<a href="%s">' % url_for(
            "manage_admin_unit.events", id=g.manage_admin_unit.id
        )
        search_close = "</a>"

        return Markup(
            lazy_gettext(
                "Here you can find your recommendation requests to other organizations. To ask another organization for a recommendation, select %(request_open)s%(request_title)s%(request_close)s on one of your event pages that you can find through the %(search_open)ssearch%(search_close)s.",
                request_open=request_open,
                request_close=request_close,
                request_title=request_title,
                search_open=search_open,
                search_close=search_close,
            )
        )


class CreateView(BaseCreateView):
    form_class = CreateForm
    organization_service: Annotated[
        organization_service.OrganizationService,
        Provide["services.organization_service"],
    ]

    def get_instruction(self, **kwargs):
        return lazy_gettext(
            "Ask another organization to reference your event on their calendar."
        )

    def check_access(self, **kwargs):
        response = super().check_access(**kwargs)
        if response:  # pragma: no cover
            return response

        event_id = int(kwargs.get("event_id", 0))
        event = Event.query.get_or_404(event_id)

        if not can_request_event_reference(event):
            abort(401)

        self.event = event

    def complete_object(self, object, form):
        super().complete_object(object, form)
        object.event = self.event

    def insert_object(self, object, form):
        self.organization_service.insert_outgoing_event_reference_request(object)

    def get_success_text(self, object, form):
        return get_success_text_for_request_creation(object)

    def get_redirect_url(self, **kwargs):
        return self.handler.get_list_url(**kwargs)
