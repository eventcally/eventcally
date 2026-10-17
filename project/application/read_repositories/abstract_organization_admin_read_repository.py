import abc
from typing import Optional

from project.application.queries.list_organizations_for_admin_query import (
    ListOrganizationsForAdminQuery,
)
from project.application.read_models.organization_admin_read_models import (
    OrganizationAdminReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationAdminReadRepository(abc.ABC):
    @abc.abstractmethod
    def list(
        self, query: ListOrganizationsForAdminQuery
    ) -> Page[OrganizationAdminReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationAdminReadModel]:  # pragma: no cover
        raise NotImplementedError
