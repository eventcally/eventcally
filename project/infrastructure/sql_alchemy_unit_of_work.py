from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import Session

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.infrastructure.repositories import (
    SqlAlchemyApiKeyRepository,
    SqlAlchemyAppKeyRepository,
    SqlAlchemyCustomWidgetRepository,
    SqlAlchemyEventOrganizerRepository,
    SqlAlchemyEventPlaceRepository,
    SqlAlchemyEventReferenceRepository,
    SqlAlchemyEventReferenceRequestRepository,
    SqlAlchemyEventRepository,
    SqlAlchemyMemberInvitationRepository,
    SqlAlchemyOAuth2ClientRepository,
    SqlAlchemyOAuth2TokenRepository,
    SqlAlchemyOrganizationInvitationRepository,
    SqlAlchemyOrganizationRelationRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyOrganizationVerificationRequestRepository,
)
from project.infrastructure.repositories.sql_alchemy_app_repository import (
    SqlAlchemyAppRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_app_installation_repository import (
    SqlAlchemyOrganizationAppInstallationRepository,
)
from project.infrastructure.repositories.sql_alchemy_organization_member_repository import (
    SqlAlchemyOrganizationMemberRepository,
)
from project.infrastructure.repositories.sql_alchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from project.infrastructure.repositories.sql_alchemy_webhook_delivery_attempt_repository import (
    SqlAlchemyWebhookDeliveryAttemptRepository,
)
from project.infrastructure.repositories.sql_alchemy_webhook_delivery_repository import (
    SqlAlchemyWebhookDeliveryRepository,
)
from project.infrastructure.repositories.sql_alchemy_webhook_repository import (
    SqlAlchemyWebhookEventRepository,
)
from project.infrastructure.sql_error_translation import (
    raise_domain_error_from_sql_error,
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, scoped_session_or_factory):
        super().__init__()
        if isinstance(scoped_session_or_factory, scoped_session):
            self.session_factory = scoped_session_or_factory
            self.is_scoped = True
        else:  # pragma: no cover
            self.session_factory = scoped_session_or_factory
            self.is_scoped = False

        self.session: Session = (
            self.session_factory() if not self.is_scoped else self.session_factory
        )
        self.events = SqlAlchemyEventRepository(self.session)
        self.event_organizers = SqlAlchemyEventOrganizerRepository(self.session)
        self.event_references = SqlAlchemyEventReferenceRepository(self.session)
        self.event_reference_requests = SqlAlchemyEventReferenceRequestRepository(
            self.session
        )
        self.event_places = SqlAlchemyEventPlaceRepository(self.session)
        self.organizations = SqlAlchemyOrganizationRepository(self.session)
        self.organization_relations = SqlAlchemyOrganizationRelationRepository(
            self.session
        )
        self.organization_verification_requests = (
            SqlAlchemyOrganizationVerificationRequestRepository(self.session)
        )
        self.webhook_events = SqlAlchemyWebhookEventRepository(self.session)
        self.webhook_deliveries = SqlAlchemyWebhookDeliveryRepository(self.session)
        self.webhook_delivery_attempts = SqlAlchemyWebhookDeliveryAttemptRepository(
            self.session
        )
        self.users = SqlAlchemyUserRepository(self.session)
        self.apps = SqlAlchemyAppRepository(self.session)
        self.organization_app_installations = (
            SqlAlchemyOrganizationAppInstallationRepository(self.session)
        )
        self.organization_members = SqlAlchemyOrganizationMemberRepository(self.session)
        self.custom_widgets = SqlAlchemyCustomWidgetRepository(self.session)
        self.api_keys = SqlAlchemyApiKeyRepository(self.session)
        self.app_keys = SqlAlchemyAppKeyRepository(self.session)
        self.oauth2_clients = SqlAlchemyOAuth2ClientRepository(self.session)
        self.oauth2_tokens = SqlAlchemyOAuth2TokenRepository(self.session)
        self.organization_invitations = SqlAlchemyOrganizationInvitationRepository(
            self.session
        )
        self.member_invitations = SqlAlchemyMemberInvitationRepository(self.session)

    def _commit(self):
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            self._reraiseSqlErrorMessage(e)

    def rollback(self):
        self.session.rollback()

    def _reraiseSqlErrorMessage(self, e: SQLAlchemyError):
        raise_domain_error_from_sql_error(e)
