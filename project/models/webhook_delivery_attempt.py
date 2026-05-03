from project.extensions import db
from project.models.webhook_delivery_attempt_generated import (
    WebhookDeliveryAttemptGeneratedMixin,
)


class WebhookDeliveryAttempt(db.Model, WebhookDeliveryAttemptGeneratedMixin):
    pass
