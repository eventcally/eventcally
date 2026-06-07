from __future__ import annotations

from typing import Optional

from project.domain import events
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class AppAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    name: str
    app_permissions: list[str]
    redirect_uris: Optional[list[str]] = None
    scope: Optional[str] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    setup_url: Optional[str] = None
    webhook: Optional[WebhookValueObject] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        name: str,
        app_permissions: list[str],
        redirect_uris: Optional[list[str]] = None,
        scope: Optional[str] = None,
        description: Optional[str] = None,
        homepage_url: Optional[str] = None,
        setup_url: Optional[str] = None,
        webhook: Optional[WebhookValueObject] = None,
    ) -> AppAggregate:
        instance = cls(
            id=-1,
            name=name,
            admin_unit_id=admin_unit_id,
            description=description,
            app_permissions=app_permissions,
            homepage_url=homepage_url,
            setup_url=setup_url,
            webhook=webhook,
            redirect_uris=redirect_uris,
            scope=scope,
        )

        event = events.AppCreated(
            actor=actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            name=instance.name,
            app_permissions=instance.app_permissions,
            redirect_uris=instance.redirect_uris,
            scope=instance.scope,
            description=instance.description,
            homepage_url=instance.homepage_url,
            setup_url=instance.setup_url,
            webhook=instance.webhook,
        )

        instance.domain_events.append(event)
        return instance

    def update(
        self,
        actor: Actor,
        name: Unsetable[str] = unset,
        app_permissions: Unsetable[list[str]] = unset,
        redirect_uris: NullableUnsetable[list[str]] = unset,
        scope: Unsetable[str] = unset,
        description: NullableUnsetable[str] = unset,
        homepage_url: NullableUnsetable[str] = unset,
        setup_url: NullableUnsetable[str] = unset,
        webhook: NullableUnsetable[WebhookValueObject] = unset,
    ):
        event = events.AppUpdated(
            actor=actor,
            id=self.id,
            admin_unit_id=self.admin_unit_id,
        )

        self._update_field_with_value("name", name, event)
        self._update_field_with_value("app_permissions", app_permissions, event)
        self._update_field_with_value("redirect_uris", redirect_uris, event)
        self._update_field_with_value("scope", scope, event)
        self._update_field_with_value("description", description, event)
        self._update_field_with_value("homepage_url", homepage_url, event)
        self._update_field_with_value("setup_url", setup_url, event)
        self._update_field_with_value("webhook", webhook, event)

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete_app(self, actor: Actor):
        self.domain_events.append(
            events.AppDeleted(actor=actor, id=self.id, admin_unit_id=self.admin_unit_id)
        )
