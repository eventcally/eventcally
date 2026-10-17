import abc
from typing import Optional

from project.application.queries.list_verifier_organizations_query import (
    ListVerifierOrganizationsQuery,
)
from project.application.queries.search_organizations_query import (
    SearchOrganizationsQuery,
)
from project.application.read_models.event_read_models import (
    VerifierOrganizationReadModel,
)
from project.application.read_models.organization_read_models import (
    OrganizationDetailReadModel,
    OrganizationListItemReadModel,
    OrganizationWidgetSettingsReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationReadRepository(abc.ABC):
    @abc.abstractmethod
    def search(
        self, query: SearchOrganizationsQuery
    ) -> Page[OrganizationListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_widget_settings(
        self, object_id: ObjectId
    ) -> Optional[OrganizationWidgetSettingsReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_verifiers(
        self, query: ListVerifierOrganizationsQuery
    ) -> Page[VerifierOrganizationReadModel]:  # pragma: no cover
        raise NotImplementedError
