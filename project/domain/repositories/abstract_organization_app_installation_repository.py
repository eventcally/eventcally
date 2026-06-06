import abc
from typing import Set

from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.types.object_id import ObjectId


class AbstractOrganizationAppInstallationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OrganisationAppInstallationAggregate] = set()

    def add(self, app: OrganisationAppInstallationAggregate):
        self._add(app)
        self.seen.add(app)

    def update(self, app: OrganisationAppInstallationAggregate):
        self._update(app)
        self.seen.add(app)

    def get(self, object_id: int) -> OrganisationAppInstallationAggregate:
        app = self._get(object_id)
        if app:
            self.seen.add(app)
        return app

    def remove(self, app: OrganisationAppInstallationAggregate):
        self._remove(app)
        self.seen.add(app)

    def get_all_with_webhook(
        self, admin_unit_id: ObjectId, permissions: list[str], event_type: str
    ) -> list[OrganisationAppInstallationAggregate]:
        installations = self._get_all_with_webhook(admin_unit_id, event_type)
        return [
            i
            for i in installations
            if all(p in (i.permissions or []) for p in permissions)
        ]

    @abc.abstractmethod
    def _add(self, app: OrganisationAppInstallationAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, app: OrganisationAppInstallationAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> OrganisationAppInstallationAggregate:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, app: OrganisationAppInstallationAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_all_with_webhook(
        self, admin_unit_id: ObjectId, event_type: str
    ) -> list[OrganisationAppInstallationAggregate]:  # pragma: no cover
        raise NotImplementedError
