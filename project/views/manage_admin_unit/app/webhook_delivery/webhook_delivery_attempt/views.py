from flask import g, redirect

from project.domain.commands.attempt_to_deliver_webhook_command import (
    AttemptToDeliverWebhookCommand,
)
from project.modular.base_form import BaseCreateForm
from project.modular.base_views import BaseCreateView
from project.views.utils import handle_base_error


class CreateView(BaseCreateView):
    form_class = BaseCreateForm

    @handle_base_error
    def dispatch_validated_form(self, form, object, **kwargs):
        cmd = AttemptToDeliverWebhookCommand.model_construct(
            webhook_delivery_id=g.current_webhook_delivery.id
        )
        self.message_bus.dispatch_command(cmd)

        self.flash_success_message(object, form)
        return redirect(self.get_redirect_url(object=object))
