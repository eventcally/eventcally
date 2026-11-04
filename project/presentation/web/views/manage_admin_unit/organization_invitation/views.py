from project.presentation.web.views.manage_admin_unit.shell_views import (
    CreateShellView,
    ListShellView,
    UpdateShellView,
)


class CreateView(CreateShellView):
    """A shell: the Vue page reads and saves through `/bff/manage`."""


class UpdateView(UpdateShellView):
    """A shell, see `CreateView`."""


class ListView(ListShellView):
    """A shell: the Vue page lists through `/bff/manage`."""
