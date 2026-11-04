from project.presentation.web.views.manage_admin_unit.shell_views import (
    CreateShellView,
    ListShellView,
    ReadShellView,
)


class CreateView(CreateShellView):
    """A shell: the Vue page saves through `/bff/manage`."""


class ListView(ListShellView):
    """A shell: the Vue page lists through `/bff/manage`."""


class ReadView(ReadShellView):
    """A shell, see `ListView`."""
