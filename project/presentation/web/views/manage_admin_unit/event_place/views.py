from project.presentation.web.views.manage_admin_unit.shell_views import (
    CreateShellView,
    UpdateShellView,
)


class CreateView(CreateShellView):
    """A shell: the Vue page reads and saves through `/bff/manage`."""


class UpdateView(UpdateShellView):
    """A shell, see `CreateView`."""
