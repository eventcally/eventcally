from project.application.queries import GetAppWebhookDeliveryQuery
from project.presentation.web.views.manage_admin_unit.app import app_bp
from project.presentation.web.views.manage_admin_unit.app.child_view_handler import (
    AppChildViewHandler,
)
from project.presentation.web.views.manage_admin_unit.app.view_handler import (
    handler as app_view_handler,
)
from project.presentation.web.views.manage_admin_unit.shell_views import (
    ListShellView,
    ReadShellView,
)


class ListView(ListShellView):
    """A shell: the Vue page lists through `/bff/manage`."""


class ReadView(ReadShellView):
    """A shell: the Vue page shows the delivery and its attempts through
    `/bff/manage`."""


class WebhookDeliveryViewHandler(AppChildViewHandler):
    app_id_attribute_name = "app_id"
    model_name = "webhook_delivery"
    model_name_plural = "webhook_deliveries"
    display_name = "Webhook delivery"
    display_name_plural = "Webhook deliveries"
    create_view_class = None
    update_view_class = None
    delete_view_class = None
    list_view_class = ListView
    read_view_class = ReadView

    def create_get_query(self, object_id):
        return GetAppWebhookDeliveryQuery(id=object_id)

    def get_object_title(self, object):
        # Parity with the ORM `CustomModel.__str__`.
        return f"{self.get_model_display_name()} {object.id}"


handler = WebhookDeliveryViewHandler(parent=app_view_handler)
handler.init_app(app_bp)
