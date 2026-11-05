from flask import abort

from project.application.queries import GetInstallableAppQuery
from project.presentation.web.views.manage_admin_unit.shell_views import (
    CreateShellView,
    ListShellView,
    ReadShellView,
)


class ListView(ListShellView):
    """A shell: the Vue page lists through `/bff/manage`."""


class ReadView(ReadShellView):
    """A shell: the Vue page shows the installation, accepts the permissions and
    uninstalls through `/bff/manage`."""


class InstallView(CreateShellView):
    """A shell: the entry point an app links its users to. The Vue page installs
    through `/bff/manage`."""

    def dispatch_request(self, **kwargs):
        if (
            self.query_bus.handle(GetInstallableAppQuery(id=kwargs.get("app_id")))
            is None
        ):
            abort(404)

        return super().dispatch_request(**kwargs)
