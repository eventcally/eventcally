from typing import Optional

from project.domain.events.app_installation_created import AppInstallationCreated
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)
from project.domain.repositories.abstract_organization_app_installation_repository import (
    AbstractOrganizationAppInstallationRepository,
)
from project.models.app import AppInstallation
from project.models.oauth import OAuth2Client
from project.models.webhook import Webhook


class SqlAlchemyOrganizationAppInstallationRepository(
    AbstractOrganizationAppInstallationRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, app: OrganisationAppInstallationAggregate):
        model = AppInstallation.from_aggregate(app)
        self.session.add(model)
        self.session.flush()

        domain_event = app.get_first_domain_event_by_type(AppInstallationCreated)
        app.id = model.id
        domain_event.id = model.id

    def _update(self, app: OrganisationAppInstallationAggregate):
        model = self._get_model(app.id)
        model.fill_from_aggregate(app)
        self.session.merge(model)
        self.session.flush()

    def _get_model(self, object_id: int) -> AppInstallation:
        return (
            self.session.query(AppInstallation)
            .filter(AppInstallation.id == object_id)
            .first()
        )

    def _get(self, object_id: int) -> Optional[OrganisationAppInstallationAggregate]:
        model = self._get_model(object_id)
        return AppInstallation.to_aggregate(model)

    def _get_all_with_webhook(
        self, admin_unit_id: int, event_type: str
    ) -> list[OrganisationAppInstallationAggregate]:
        models = (
            self.session.query(AppInstallation)
            .join(AppInstallation.oauth2_client)
            .join(OAuth2Client.webhook)
            .filter(OAuth2Client.is_app)
            .filter(AppInstallation.admin_unit_id == admin_unit_id)
            .filter(Webhook.url.isnot(None))
            .filter(Webhook.disabled.isnot(True))
            .filter(Webhook.event_types.contains([event_type]))
            .all()
        )
        return [AppInstallation.to_aggregate(m) for m in models]

    def _remove(self, app: OrganisationAppInstallationAggregate):
        model = self._get_model(app.id)
        self.session.delete(model)
