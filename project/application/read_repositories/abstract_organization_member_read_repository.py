import abc
from typing import List, Optional

from project.application.queries.list_organization_members_query import (
    ListOrganizationMembersQuery,
)
from project.application.queries.list_user_organization_memberships_query import (
    ListUserOrganizationMembershipsQuery,
)
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberReadModel,
    OrganizationMemberRoleReadModel,
    UserOrganizationMembershipReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationMemberReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListOrganizationMembersQuery
    ) -> Page[OrganizationMemberReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationMemberReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_for_user(
        self, query: ListUserOrganizationMembershipsQuery
    ) -> Page[UserOrganizationMembershipReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_membership(
        self, object_id: ObjectId
    ) -> Optional[UserOrganizationMembershipReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_roles(self) -> List[OrganizationMemberRoleReadModel]:  # pragma: no cover
        raise NotImplementedError
