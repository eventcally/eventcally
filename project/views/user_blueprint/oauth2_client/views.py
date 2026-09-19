from flask import redirect
from flask_security import current_user

from project.application.commands import DeleteOAuth2ClientCommand
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.views.utils import handle_base_error


class CreateView(BaseCreateView):
    def build_create_command(self, form):
        return form.create_create_command(user_id=current_user.id)

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = self.build_create_command(form)
        cmd_result = self.message_bus.handle_command(cmd)
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))


class UpdateView(BaseUpdateView):
    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = form.create_update_command(object.id)
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))


class DeleteView(BaseDeleteView):
    @handle_base_error
    def dispatch_validated_form_deletable(self, form, object, **kwargs):
        cmd = DeleteOAuth2ClientCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
