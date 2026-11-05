from flask import abort, g
from flask_babel import gettext
from flask_security import auth_required

from project.application.queries import GetAppWebhookDeliveryQuery
from project.presentation.web.views.manage_admin_unit.app import app_bp
from project.presentation.web.views.manage_admin_unit.shell_views import (
    owned_object_or_abort,
    render_manage_shell,
)
from project.presentation.web.views.utils import manage_permission_required


@app_bp.route("/webhook_deliveries")
@auth_required()
@manage_permission_required("webhook_deliveries:read")
def webhook_deliveries():
    return render_manage_shell(gettext("Webhook deliveries"))


@app_bp.route("/webhook_delivery/<int:webhook_delivery_id>")
@auth_required()
@manage_permission_required("webhook_deliveries:read")
def webhook_delivery(webhook_delivery_id):
    delivery = owned_object_or_abort(GetAppWebhookDeliveryQuery(id=webhook_delivery_id))

    if delivery.app_id != g.current_app.id:
        abort(401)

    return render_manage_shell(f"{gettext('Webhook delivery')} {delivery.id}")
