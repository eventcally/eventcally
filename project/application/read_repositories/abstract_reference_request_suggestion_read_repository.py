import abc
from typing import List

from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class AbstractReferenceRequestSuggestionReadRepository(abc.ABC):
    """The four ordered suggestion sources. Each returns at most `limit` organizations
    that accept incoming reference requests, in suggestion order."""

    @abc.abstractmethod
    def newest_requested_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:  # pragma: no cover
        """Targets of the newest outgoing reference requests."""
        raise NotImplementedError

    @abc.abstractmethod
    def newest_referencing_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:  # pragma: no cover
        """Organizations that referenced events of the newest outgoing references."""
        raise NotImplementedError

    @abc.abstractmethod
    def related_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:  # pragma: no cover
        """Sources of inbound relations, auto verifying and verifying ones first."""
        raise NotImplementedError

    @abc.abstractmethod
    def other_organizations(
        self, admin_unit_id: ObjectId, limit: int
    ) -> List[OrganizationRefReadModel]:  # pragma: no cover
        """Any other organization that accepts reference requests."""
        raise NotImplementedError
