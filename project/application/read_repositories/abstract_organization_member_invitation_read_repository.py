import abc
from typing import Optional

from project.application.queries.list_organization_member_invitations_query import (
    ListOrganizationMemberInvitationsQuery,
)
from project.application.queries.list_user_member_invitations_query import (
    ListUserMemberInvitationsQuery,
)
from project.application.read_models.organization_member_invitation_read_models import (
    OrganizationMemberInvitationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationMemberInvitationReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListOrganizationMemberInvitationsQuery
    ) -> Page[OrganizationMemberInvitationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationMemberInvitationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_for_user(
        self, query: ListUserMemberInvitationsQuery
    ) -> Page[OrganizationMemberInvitationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipient_email(
        self, object_id: ObjectId
    ) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError
