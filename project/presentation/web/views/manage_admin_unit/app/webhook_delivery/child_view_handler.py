from flask import abort, g

from project.presentation.web.views.manage_admin_unit.app.child_view_handler import (
    AppChildViewHandler,
)
from project.shared.utils import getattr_keypath


class WebhookDeliveryChildViewHandler(AppChildViewHandler):
    app_id_attribute_name = "app_id"
    webhook_delivery_id_attribute_name = "webhook_delivery_id"

    def check_object_access(self, object):
        super().check_object_access(object)

        if (
            not getattr_keypath(object, self.webhook_delivery_id_attribute_name)
            == g.current_webhook_delivery.id
        ):
            abort(401)

    def get_breadcrumbs(self):
        result = super().get_breadcrumbs()

        result.append(
            self._create_breadcrumb(
                self.parent.get_list_url(),
                self.parent.get_model_display_name_plural(),
            )
        )
        result.append(
            self._create_breadcrumb(
                self.parent.get_read_url(g.current_webhook_delivery),
                self.parent.get_object_title(g.current_webhook_delivery),
            )
        )

        return result
