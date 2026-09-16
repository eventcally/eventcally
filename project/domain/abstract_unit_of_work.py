from __future__ import annotations

import abc
from typing import List

from project.domain.events import Event
from project.domain.repositories import (
    AbstractApiKeyRepository,
    AbstractCustomWidgetRepository,
    AbstractEventOrganizerRepository,
    AbstractEventPlaceRepository,
    AbstractEventReferenceRepository,
    AbstractEventRepository,
    AbstractOAuth2ClientRepository,
    AbstractOAuth2TokenRepository,
    AbstractOrganizationRelationRepository,
    AbstractOrganizationRepository,
    AbstractOrganizationVerificationRequestRepository,
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
    organization_relations: AbstractOrganizationRelationRepository
    organization_verification_requests: (
        AbstractOrganizationVerificationRequestRepository
    )
    webhook_events: AbstractWebhookEventRepository
    webhook_deliveries: AbstractWebhookDeliveryRepository
    webhook_delivery_attempts: AbstractWebhookDeliveryAttemptRepository
    apps: AbstractAppRepository
    organization_app_installations: AbstractOrganizationAppInstallationRepository
    organization_members: AbstractOrganizationMemberRepository
    users: AbstractUserRepository
    custom_widgets: AbstractCustomWidgetRepository
    api_keys: AbstractApiKeyRepository
    oauth2_clients: AbstractOAuth2ClientRepository
    oauth2_tokens: AbstractOAuth2TokenRepository

    def __init__(self):
        self.pending_events: List[Event] = []

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
        self._collect_domain_events_from_repo(self.organization_relations)
        self._collect_domain_events_from_repo(self.organization_verification_requests)
        self._collect_domain_events_from_repo(self.webhook_events)
        self._collect_domain_events_from_repo(self.apps)
        self._collect_domain_events_from_repo(self.organization_app_installations)
        self._collect_domain_events_from_repo(self.organization_members)
        self._collect_domain_events_from_repo(self.webhook_deliveries)
        self._collect_domain_events_from_repo(self.webhook_delivery_attempts)
        self._collect_domain_events_from_repo(self.users)
        self._collect_domain_events_from_repo(self.custom_widgets)
        self._collect_domain_events_from_repo(self.api_keys)
        self._collect_domain_events_from_repo(self.oauth2_clients)
        self._collect_domain_events_from_repo(self.oauth2_tokens)

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
