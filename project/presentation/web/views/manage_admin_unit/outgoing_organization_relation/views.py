from flask import redirect, render_template

from project.application.commands import DeleteOrganizationRelationCommand
from project.presentation.shared.current_admin_unit import current_admin_unit
from project.presentation.web.boot import build_boot_data
from project.presentation.web.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseUpdateView,
)
from project.presentation.web.views.utils import handle_base_error


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not current_admin_unit.can_verify_other:
            del form.verify

        return form


def _render_shell(title):
    return render_template(
        "manage/organization_relation_form.html",
        entry="manage",
        title=title,
        boot=build_boot_data(base="/"),
    )


class CreateView(BaseCreateView):
    """A shell: the Vue page reads and saves through `/bff/manage`."""

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        return _render_shell(self.get_title())


class UpdateView(BaseUpdateView):
    """A shell, see `CreateView`."""

    def dispatch_request(self, **kwargs):
        response = self.check_access(**kwargs)

        if response:  # pragma: no cover
            return response

        object = self.get_object_from_kwargs(**kwargs)
        response = self.check_object_access(object)

        if response:  # pragma: no cover
            return response

        return _render_shell(self.get_title())


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteOrganizationRelationCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())


class ListView(SharedFormViewMixin, BaseListView):
    def create_display(self, **kwargs):
        display = super().create_display(**kwargs)

        if not current_admin_unit.can_verify_other:
            del display.verify

        return display
