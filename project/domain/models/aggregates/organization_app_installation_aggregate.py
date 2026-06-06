from __future__ import annotations

from project.domain.events.app_installation_created import AppInstallationCreated
from project.domain.events.app_installation_deleted import AppInstallationDeleted
from project.domain.events.app_installation_permissions_updated import (
    AppInstallationPermissionsUpdated,
)
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class OrganisationAppInstallationAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    app_id: ObjectId
    permissions: list[str]

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        app_id: ObjectId,
        permissions: list[str],
    ) -> OrganisationAppInstallationAggregate:
        instance = cls(
            id=-1, admin_unit_id=admin_unit_id, app_id=app_id, permissions=permissions
        )

        event = AppInstallationCreated(
            actor=actor,
            id=-1,
            admin_unit_id=instance.admin_unit_id,
            app_id=instance.app_id,
            permissions=instance.permissions,
        )

        instance.domain_events.append(event)
        return instance

    def update_permissions(self, actor: Actor, permissions: list[str]):
        event = AppInstallationPermissionsUpdated(
            actor=actor,
            id=self.id,
            admin_unit_id=self.admin_unit_id,
            app_id=self.app_id,
        )

        self._update_field_with_value("permissions", permissions, event)

        if event.has_changed_values():
            self.domain_events.append(event)

    def delete(self, actor: Actor):
        self.domain_events.append(
            AppInstallationDeleted(
                actor=actor,
                id=self.id,
                admin_unit_id=self.admin_unit_id,
                app_id=self.app_id,
            )
        )
