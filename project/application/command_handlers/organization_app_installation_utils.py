from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.organization_app_installation_aggregate import (
    OrganisationAppInstallationAggregate,
)


def ensure_organization_app_installation_exists(
    app_installation_id: int, uow: AbstractUnitOfWork
) -> OrganisationAppInstallationAggregate:
    app_installation = uow.organization_app_installations.get(app_installation_id)

    if not app_installation:
        raise NotFoundError(f"App installation with id {app_installation_id} not found")

    return app_installation
