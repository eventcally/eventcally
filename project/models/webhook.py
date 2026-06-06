from sqlalchemy.event import listens_for

from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.extensions import db
from project.models.iowned import IOwned
from project.models.webhook_generated import WebhookGeneratedMixin


class Webhook(db.Model, WebhookGeneratedMixin, IOwned):
    def fill_from_value_object(self, value: WebhookValueObject):
        self.url = value.url
        self.secret = value.secret
        self.disabled = value.disabled
        self.event_types = value.event_types

    def to_value_object(self) -> WebhookValueObject:
        return WebhookValueObject(
            url=self.url,
            secret=self.secret,
            disabled=self.disabled,
            event_types=self.event_types,
        )

    def is_enabled_for_event_type(self, event_type: str) -> bool:
        return (
            self.url
            and not self.disabled
            and (self.event_types and event_type in self.event_types)
        )

    def validate(self):
        if not self.url:
            raise ValueError("URL is required for a webhook")

    def is_empty(self):
        return not self.url

    def before_flush(self, session, is_dirty):
        if self.is_empty():
            if self.app:
                self.app.logo = None


@listens_for(Webhook, "before_insert")
@listens_for(Webhook, "before_update")
def before_saving_webhook(mapper, connect, self):
    self.validate()
