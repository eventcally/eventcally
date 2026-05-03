from typing import Optional

from sqlalchemy.event import listens_for

from project.domain import events
from project.domain.commands.create_webhook import CreateWebhook
from project.domain.commands.update_webhook import UpdateWebhook
from project.domain.types import unset
from project.domain.types.unsetable import Unsetable
from project.extensions import db
from project.models.iowned import IOwned
from project.models.webhook_generated import WebhookGeneratedMixin


class Webhook(db.Model, WebhookGeneratedMixin, IOwned):
    @classmethod
    def create(
        cls,
        cmd: Optional[CreateWebhook],
        parent,
        parent_event: events.Event,
        field_name: str,
        event_field_name: Optional[str] = None,
    ):
        if cmd is None:
            return

        if event_field_name is None:
            event_field_name = field_name

        instance = cls()
        instance.url = cmd.url
        instance.secret = cmd.secret
        instance.disabled = cmd.disabled
        instance.event_types = cmd.event_types
        instance.validate()
        setattr(parent, field_name, instance)

        event = events.WebhookCreated(
            url=instance.url,
            secret=instance.secret,
            disabled=instance.disabled,
            event_types=instance.event_types,
        )
        setattr(parent_event, event_field_name, event)

    @classmethod
    def update(
        cls,
        cmd: Unsetable[UpdateWebhook],
        parent,
        parent_event: events.Event,
        field_name: str,
        event_field_name: Optional[str] = None,
    ):
        if cmd == unset:
            return

        if event_field_name is None:
            event_field_name = field_name

        instance: Webhook = getattr(parent, field_name)

        if cmd is None:
            if instance is not None:
                setattr(parent, field_name, None)
                setattr(parent_event, event_field_name, None)
            return

        if instance is None:
            instance = cls()

        event = events.WebhookUpdated()
        instance._update_field(cmd, event, "url")
        instance._update_field(cmd, event, "secret")
        instance._update_field(cmd, event, "disabled")
        instance._update_field(cmd, event, "event_types")
        instance.validate()

        setattr(parent, field_name, instance)

        if event.has_changed_values():
            setattr(parent_event, event_field_name, event)

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
