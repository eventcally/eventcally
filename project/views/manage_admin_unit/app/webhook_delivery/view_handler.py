from flask import g

from project.application.queries import (
    GetAppWebhookDeliveryQuery,
    ListAppWebhookDeliveriesQuery,
)
from project.views.manage_admin_unit.app import app_bp
from project.views.manage_admin_unit.app.child_view_handler import AppChildViewHandler
from project.views.manage_admin_unit.app.view_handler import handler as app_view_handler
from project.views.manage_admin_unit.app.webhook_delivery.displays import (
    ListDisplay,
    ReadDisplay,
)


class WebhookDeliveryViewHandler(AppChildViewHandler):
    app_id_attribute_name = "app_id"
    model_name = "webhook_delivery"
    model_name_plural = "webhook_deliveries"
    display_name = "Webhook delivery"
    display_name_plural = "Webhook deliveries"
    create_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    read_display_class = ReadDisplay

    def create_list_query(self, form, page_request, **kwargs):
        return ListAppWebhookDeliveriesQuery(app_id=g.current_app.id, page=page_request)

    def create_get_query(self, object_id):
        return GetAppWebhookDeliveryQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = WebhookDeliveryViewHandler(parent=app_view_handler)
handler.init_app(app_bp)
