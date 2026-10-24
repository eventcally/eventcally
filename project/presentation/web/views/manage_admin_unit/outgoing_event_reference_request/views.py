from flask import abort, g, render_template, url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup

from project.application.queries import GetEventDetailQuery
from project.presentation.shared.access import can_request_event_reference
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.modular.base_views import BaseCreateView, BaseListView


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
    """A shell: the Vue page reads and saves through `/bff/manage`."""

    def check_access(self, **kwargs):
        response = super().check_access(**kwargs)
        if response:  # pragma: no cover
            return response

        event_id = int(kwargs.get("event_id", 0))
        event = result_or_404(self.query_bus.handle(GetEventDetailQuery(id=event_id)))

        if not can_request_event_reference(event):
            abort(401)

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        return render_template(
            "manage/reference_request_form.html",
            entry="manage",
            title=self.get_title(),
            boot=build_boot_data(base="/"),
        )
