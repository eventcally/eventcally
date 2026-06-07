from project.models import WebhookDeliveryAttempt
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
    admin_unit_id_attribute_name = "webhook_delivery.app.admin_unit_id"
    app_id_attribute_name = "webhook_delivery.app_id"
    model = WebhookDeliveryAttempt
    create_view_class = CreateView
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    read_display_class = ReadDisplay

    def get_object_by_id(self, object_id):
        with self.message_bus.create_uow() as uow:
            return uow.webhook_delivery_attempts._get_model(object_id)

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(WebhookDeliveryAttempt.id)
        )


handler = WebhookDeliveryAttemptViewHandler(parent=webhook_delivery_view_handler)
handler.init_app(webhook_delivery_bp)
