from __future__ import annotations

import abc
from typing import List

from project.domain.events import Event
from project.domain.repositories import (
    AbstractEventOrganizerRepository,
    AbstractEventPlaceRepository,
    AbstractEventReferenceRepository,
    AbstractEventRepository,
    AbstractOrganizationRepository,
)
from project.domain.repositories.abstract_app_repository import AbstractAppRepository
from project.domain.repositories.abstract_organization_app_installation_repository import (
    AbstractOrganizationAppInstallationRepository,
)
from project.domain.repositories.abstract_organization_member_repository import (
    AbstractOrganizationMemberRepository,
)
from project.domain.repositories.abstract_user_repository import AbstractUserRepository
from project.domain.repositories.abstract_webhook_delivery_attempt_repository import (
    AbstractWebhookDeliveryAttemptRepository,
)
from project.domain.repositories.abstract_webhook_delivery_repository import (
    AbstractWebhookDeliveryRepository,
)
from project.domain.repositories.abstract_webhook_event_repository import (
    AbstractWebhookEventRepository,
)


class AbstractUnitOfWork(abc.ABC):
    events: AbstractEventRepository
    event_organizers: AbstractEventOrganizerRepository
    event_references: AbstractEventReferenceRepository
    event_places: AbstractEventPlaceRepository
    organizations: AbstractOrganizationRepository
    webhook_events: AbstractWebhookEventRepository
    webhook_deliveries: AbstractWebhookDeliveryRepository
    webhook_delivery_attempts: AbstractWebhookDeliveryAttemptRepository
    apps: AbstractAppRepository
    organization_app_installations: AbstractOrganizationAppInstallationRepository
    organization_members: AbstractOrganizationMemberRepository
    users: AbstractUserRepository
    pending_events: List[Event] = []

    def __enter__(self) -> AbstractUnitOfWork:
        self.pending_events = []
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc:
            self.pending_events.clear()

        self.rollback()

    def commit(self):
        self._commit()
        self._collect_domain_events()

    def collect_pending_events(self) -> List[Event]:
        result = list(self.pending_events)
        self.pending_events.clear()
        return result

    def get_first_pending_event_by_type(self, event_type: type) -> Event | None:
        for event in self.pending_events:
            if isinstance(event, event_type):
                return event
        return None  # pragma: no cover

    def _collect_domain_events(self):
        self._collect_domain_events_from_repo(self.events)
        self._collect_domain_events_from_repo(self.event_organizers)
        self._collect_domain_events_from_repo(self.event_references)
        self._collect_domain_events_from_repo(self.event_places)
        self._collect_domain_events_from_repo(self.organizations)
        self._collect_domain_events_from_repo(self.webhook_events)
        self._collect_domain_events_from_repo(self.apps)
        self._collect_domain_events_from_repo(self.organization_app_installations)
        self._collect_domain_events_from_repo(self.organization_members)
        self._collect_domain_events_from_repo(self.webhook_deliveries)
        self._collect_domain_events_from_repo(self.webhook_delivery_attempts)
        self._collect_domain_events_from_repo(self.users)

    def _collect_domain_events_from_repo(self, repo):
        for model in repo.seen:
            self.pending_events.extend(model.domain_events)
            model.domain_events.clear()

    @abc.abstractmethod
    def _commit(self):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):  # pragma: no cover
        raise NotImplementedError
