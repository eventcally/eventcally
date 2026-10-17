import abc
from typing import Optional

from project.application.queries.list_incoming_organization_verification_requests_query import (
    ListIncomingOrganizationVerificationRequestsQuery,
)
from project.application.queries.list_outgoing_organization_verification_requests_query import (
    ListOutgoingOrganizationVerificationRequestsQuery,
)
from project.application.read_models.organization_verification_request_read_models import (
    OrganizationVerificationRequestReadModel,
    OrganizationVerificationRequestReviewReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationVerificationRequestReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_incoming(
        self, query: ListIncomingOrganizationVerificationRequestsQuery
    ) -> Page[OrganizationVerificationRequestReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_outgoing(
        self, query: ListOutgoingOrganizationVerificationRequestsQuery
    ) -> Page[OrganizationVerificationRequestReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationVerificationRequestReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_review(
        self, object_id: ObjectId
    ) -> Optional[OrganizationVerificationRequestReviewReadModel]:  # pragma: no cover
        raise NotImplementedError
