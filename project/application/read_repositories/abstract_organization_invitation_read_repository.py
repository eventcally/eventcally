import abc
from typing import Optional

from project.application.queries.list_organization_invitations_query import (
    ListOrganizationInvitationsQuery,
)
from project.application.queries.list_user_organization_invitations_query import (
    ListUserOrganizationInvitationsQuery,
)
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationDetailReadModel,
    OrganizationInvitationListItemReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOrganizationInvitationReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListOrganizationInvitationsQuery
    ) -> Page[OrganizationInvitationListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationInvitationDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_for_user(
        self, query: ListUserOrganizationInvitationsQuery
    ) -> Page[OrganizationInvitationDetailReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_recipient_email(
        self, object_id: ObjectId
    ) -> Optional[str]:  # pragma: no cover
        raise NotImplementedError
