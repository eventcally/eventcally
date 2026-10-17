from flask import g

from project.application.queries import (
    GetAppWebhookDeliveryAttemptQuery,
    ListAppWebhookDeliveryAttemptsQuery,
)
from project.views.manage_admin_unit.app.webhook_delivery import webhook_delivery_bp
from project.views.manage_admin_unit.app.webhook_delivery.child_view_handler import (
    WebhookDeliveryChildViewHandler,
)
from project.views.manage_admin_unit.app.webhook_delivery.view_handler import (
    handler as webhook_delivery_view_handler,
)
from project.views.manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt.displays import (
    ListDisplay,
    ReadDisplay,
)
from project.views.manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt.views import (
    CreateView,
)


class WebhookDeliveryAttemptViewHandler(WebhookDeliveryChildViewHandler):
    model_name = "webhook_delivery_attempt"
    model_name_plural = "webhook_delivery_attempts"
    display_name = "Webhook delivery attempt"
    display_name_plural = "Webhook delivery attempts"
    create_view_class = CreateView
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    read_display_class = ReadDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListAppWebhookDeliveryAttemptsQuery(
            webhook_delivery_id=g.current_webhook_delivery.id, page=page_request
        )

    def create_get_query(self, object_id):
        return GetAppWebhookDeliveryAttemptQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = WebhookDeliveryAttemptViewHandler(parent=webhook_delivery_view_handler)
handler.init_app(webhook_delivery_bp)
