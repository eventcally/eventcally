from flask import redirect

from project.domain.commands.delete_app_command import DeleteAppCommand
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.permissions import organization_app_permission_infos
from project.service_layer.webhooks.app_installation_webhooks import (
    app_installation_webhook_infos,
)
from project.service_layer.webhooks.app_webhooks import app_webhook_infos
from project.views.manage_admin_unit.app.forms import CreateAppForm, UpdateAppForm
from project.views.utils import handle_base_error


class SharedFormViewMixin(object):
    def create_form(self, **kwargs):
        form = super().create_form(**kwargs)

        form.app_permissions.choices = [
            (i.permission, i.label) for i in organization_app_permission_infos
        ]

        form.webhook.form.event_types.choices = [
            (i.event_type, i.event_type)
            for i in app_webhook_infos + app_installation_webhook_infos
        ]

        return form


class CreateView(SharedFormViewMixin, BaseCreateView):
    @handle_base_error
    def dispatch_validated_form(self, form: CreateAppForm, object, **kwargs):
        from project.views.utils import current_admin_unit

        cmd = form.create_create_command(current_admin_unit.id)
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))


class UpdateView(SharedFormViewMixin, BaseUpdateView):
    @handle_base_error
    def dispatch_validated_form(self, form: UpdateAppForm, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteAppCommand.model_construct(id=object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
