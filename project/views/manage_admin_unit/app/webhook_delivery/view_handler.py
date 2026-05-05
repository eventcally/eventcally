from project.models.webhook_delivery import WebhookDelivery
from project.views.manage_admin_unit.app import app_bp
from project.views.manage_admin_unit.app.child_view_handler import AppChildViewHandler
from project.views.manage_admin_unit.app.view_handler import handler as app_view_handler
from project.views.manage_admin_unit.app.webhook_delivery.displays import (
    ListDisplay,
    ReadDisplay,
)


class WebhookDeliveryViewHandler(AppChildViewHandler):
    admin_unit_id_attribute_name = "app.admin_unit_id"
    app_id_attribute_name = "app_id"
    model = WebhookDelivery
    create_view_class = None
    update_view_class = None
    delete_view_class = None
    list_display_class = ListDisplay
    read_display_class = ReadDisplay

    def get_object_by_id(self, object_id):
        with self.message_bus.create_uow() as uow:
            return uow.webhooks.get_delivery(object_id)

    def apply_objects_query_order(self, query, **kwargs):
        return (
            super()
            .apply_objects_query_order(query, **kwargs)
            .order_by(WebhookDelivery.id.desc())
        )


handler = WebhookDeliveryViewHandler(parent=app_view_handler)
handler.init_app(app_bp)
