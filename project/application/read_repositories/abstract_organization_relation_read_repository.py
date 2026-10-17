import abc
from typing import Optional

from project.application.queries.list_outgoing_organization_relations_query import (
    ListOutgoingOrganizationRelationsQuery,
)
from project.application.read_models.organization_relation_read_models import (
    OrganizationRelationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationRelationReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListOutgoingOrganizationRelationsQuery
    ) -> Page[OrganizationRelationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationRelationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_by_target(
        self, admin_unit_id: ObjectId, target_admin_unit_id: ObjectId
    ) -> Optional[OrganizationRelationReadModel]:  # pragma: no cover
        raise NotImplementedError
