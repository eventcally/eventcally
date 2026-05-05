from project.extensions import db
from project.models.webhook_event_generated import WebhookEventGeneratedMixin


class WebhookEvent(db.Model, WebhookEventGeneratedMixin):
    pass
