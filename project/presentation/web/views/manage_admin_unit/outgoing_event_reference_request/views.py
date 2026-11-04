from flask import abort, render_template

from project.application.queries import GetEventDetailQuery
from project.presentation.shared.access import can_request_event_reference
from project.presentation.shared.query_results import result_or_404
from project.presentation.web.boot import build_boot_data
from project.presentation.web.modular.base_views import BaseCreateView
from project.presentation.web.views.manage_admin_unit.shell_views import (
    ListShellView,
    ReadShellView,
)


class ListView(ListShellView):
    """A shell: the Vue page lists through `/bff/manage`."""


class ReadView(ReadShellView):
    """A shell, see `ListView`."""


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
