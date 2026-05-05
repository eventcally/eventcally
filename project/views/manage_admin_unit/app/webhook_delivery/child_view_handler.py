from flask import abort, g
from sqlalchemy.orm import class_mapper

from project.utils import getattr_keypath
from project.views.manage_admin_unit.app.child_view_handler import AppChildViewHandler


class WebhookDeliveryChildViewHandler(AppChildViewHandler):
    app_id_attribute_name = "app_id"
    webhook_delivery_id_attribute_name = "webhook_delivery_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_delivery_id_column = class_mapper(self.model).columns[
            self.webhook_delivery_id_attribute_name
        ]

    def check_object_access(self, object):
        super().check_object_access(object)

        if (
            not getattr_keypath(object, self.webhook_delivery_id_attribute_name)
            == g.current_webhook_delivery.id
        ):
            abort(401)

    def complete_object(self, object, form):
        super().complete_object(object, form)
        setattr(
            object,
            self.webhook_delivery_id_attribute_name,
            g.current_webhook_delivery.id,
        )

    def apply_base_filter(self, query, **kwargs):
        return (
            super()
            .apply_base_filter(query, **kwargs)
            .filter(self.webhook_delivery_id_column == g.current_webhook_delivery.id)
        )

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
                str(g.current_webhook_delivery),
            )
        )

        return result
