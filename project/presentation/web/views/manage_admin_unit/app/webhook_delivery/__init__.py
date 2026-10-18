from flask import current_app, g

from project.presentation.web.modular.base_blueprint import BaseBlueprint

webhook_delivery_bp = BaseBlueprint(
    "webhook_delivery",
    __name__,
    url_prefix="/webhook_delivery/<int:webhook_delivery_id>",
    template_folder="templates",
    static_folder="static",
)


@webhook_delivery_bp.url_defaults
def webhook_delivery_bp_url_defaults(endpoint, values):
    if "webhook_delivery_id" not in values:
        values.setdefault("webhook_delivery_id", g.current_webhook_delivery.id)


@webhook_delivery_bp.url_value_preprocessor
def webhook_delivery_bp_url_value_preprocessor(endpoint, values):
    from flask import abort

    from project.application.queries import GetAppWebhookDeliveryQuery
    from project.presentation.shared.access import admin_unit_owner_access_or_401

    webhook_delivery_id = values.pop("webhook_delivery_id", None)
    query_bus = current_app.container.cqrs.query_bus()
    webhook_delivery = query_bus.handle(
        GetAppWebhookDeliveryQuery(id=webhook_delivery_id)
    )

    if webhook_delivery is None:
        abort(404)

    admin_unit_owner_access_or_401(webhook_delivery.admin_unit_id)
    g.current_webhook_delivery = webhook_delivery


import project.presentation.web.views.manage_admin_unit.app.webhook_delivery.view_handler
import project.presentation.web.views.manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt.view_handler
from project.presentation.web.views.manage_admin_unit.app import app_bp

app_bp.register_blueprint(webhook_delivery_bp)
