from flask import flash, redirect
from flask_babel import lazy_gettext
from flask_security import current_user

from project.application.commands import DeleteApiKeyCommand
from project.modular.base_views import BaseCreateView, BaseDeleteView, BaseUpdateView
from project.views.utils import handle_base_error


class CreateView(BaseCreateView):
    def build_create_command(self, form):
        return form.create_create_command(user_id=current_user.id)

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = self.build_create_command(form)
        cmd_result = self.message_bus.handle_command(cmd)
        self.transient_key = cmd_result.key
        self.flash_success_message(cmd_result, form)
        return redirect(self.get_redirect_url(object=cmd_result))

    def flash_success_message(self, object, form):
        super().flash_success_message(object, form)

        text = lazy_gettext(
            "Please note the key: %(key)s. It will only be displayed once.",
            key=self.transient_key,
        )
        flash(text, "warning")


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
        cmd = DeleteApiKeyCommand(
            id=object.id, actor=self.app_context_provider.get_current_actor()
        )
        self.message_bus.handle_command(cmd)
        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url())
