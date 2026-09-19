from flask import redirect, request

from project.application.commands import DeleteOrganizationRelationCommand
from project.modular.base_views import (
    BaseCreateView,
    BaseDeleteView,
    BaseListView,
    BaseUpdateView,
)
from project.views.utils import current_admin_unit, handle_base_error


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not current_admin_unit.can_verify_other:
            del form.verify

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        if not form.is_submitted():
            target = request.args.get("target", 0, type=int)
            form.target_admin_unit.process_formdata([target])

            if form.verify:
                verify = request.args.get("verify", 0, type=int)
                if verify == 1:
                    form.verify.data = True

        return form

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_create_command(current_admin_unit.id)
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


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
