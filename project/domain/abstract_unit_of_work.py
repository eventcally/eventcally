from __future__ import annotations

import abc
from typing import List

from project.domain import events
from project.domain.repositories import (
    AbstractEventOrganizerRepository,
    AbstractEventPlaceRepository,
    AbstractOrganizationRepository,
)
from project.domain.repositories.abstract_app_repository import AbstractAppRepository
from project.domain.repositories.abstract_webhook_repository import (
    AbstractWebhookRepository,
)


class AbstractUnitOfWork(abc.ABC):
    event_organizers: AbstractEventOrganizerRepository
    event_places: AbstractEventPlaceRepository
    organizations: AbstractOrganizationRepository
    webhooks: AbstractWebhookRepository
    apps: AbstractAppRepository
    pending_events: List[events.Event] = []

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

    def collect_pending_events(self) -> List[events.Event]:
        result = list(self.pending_events)
        self.pending_events.clear()
        return result

    def get_first_pending_event_by_type(self, event_type: type) -> events.Event | None:
        for event in self.pending_events:
            if isinstance(event, event_type):
                return event
        return None  # pragma: no cover

    def _collect_domain_events(self):
        self._collect_domain_events_from_repo(self.event_organizers)
        self._collect_domain_events_from_repo(self.event_places)
        self._collect_domain_events_from_repo(self.organizations)
        self._collect_domain_events_from_repo(self.webhooks)
        self._collect_domain_events_from_repo(self.apps)

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
