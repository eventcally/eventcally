from flask import g

from project.modular.base_blueprint import BaseBlueprint

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
    from project.access import admin_unit_owner_access_or_401
    from project.models import WebhookDelivery

    webhook_delivery_id = values.pop("webhook_delivery_id", None)
    webhook_delivery = WebhookDelivery.query.get_or_404(webhook_delivery_id)
    admin_unit_owner_access_or_401(webhook_delivery.app.admin_unit_id)
    g.current_webhook_delivery = webhook_delivery


import project.views.manage_admin_unit.app.webhook_delivery.view_handler
import project.views.manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt.view_handler
from project.views.manage_admin_unit.app import app_bp

app_bp.register_blueprint(webhook_delivery_bp)
