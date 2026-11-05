from flask import render_template

from project.presentation.web.boot import build_boot_data
from project.presentation.web.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseObjectFormView,
    BaseReadView,
    BaseUpdateView,
)


def render_manage_shell(title, **context):
    """The Vue 3 frame of the `manage` entry; the page reads and writes via `/bff/manage`."""
    return render_template(
        "manage/shell.html",
        entry="manage",
        title=title,
        boot=build_boot_data(base="/"),
        **context,
    )


class ShellViewMixin:
    """Turns a modular view into a shell: it keeps the endpoint and the server side
    guards (permission, foreign object 401/404, module specific
    `check_object_access`) and answers `GET` with the Vue frame."""

    methods = ["GET"]

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        title_kwargs = {}

        # The create views have no object.
        if isinstance(self, (BaseReadView, BaseObjectFormView)):
            object = self.get_object_from_kwargs(**kwargs)
            response = self.check_object_access(object)

            if response:  # pragma: no cover
                return response

            title_kwargs["object"] = object

        return render_manage_shell(self.get_title(**title_kwargs))


class ListShellView(ShellViewMixin, BaseListView):
    pass


class ReadShellView(ShellViewMixin, BaseReadView):
    pass


class CreateShellView(ShellViewMixin, BaseCreateView):
    pass


class UpdateShellView(ShellViewMixin, BaseUpdateView):
    pass


class DeleteShellView(ShellViewMixin, BaseDeleteView):
    pass
