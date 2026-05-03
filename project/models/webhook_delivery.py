from __future__ import annotations

from project.extensions import db
from project.models.webhook_delivery_generated import WebhookDeliveryGeneratedMixin


class WebhookDelivery(db.Model, WebhookDeliveryGeneratedMixin):
    pass
