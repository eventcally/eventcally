from project.presentation.web.views.manage_admin_unit.shell_views import (
    CreateShellView,
    ListShellView,
)


class CreateView(CreateShellView):
    """A shell: the Vue page reads and saves through `/bff/manage`."""


class ListView(ListShellView):
    """A shell: the Vue page lists through `/bff/manage`."""
