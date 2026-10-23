import abc
from typing import List, Optional

from project.application.queries.get_resource_owner_query import ResourceKind
from project.application.read_models.access_helper_read_models import (
    MailRecipientReadModel,
    ManageMenuOptionsReadModel,
)
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.application.read_models.current_organization_read_models import (
    CurrentOrganizationReadModel,
    OrganizationSettingsReadModel,
)
from project.domain.types.object_id import ObjectId


class AbstractAccessReadRepository(abc.ABC):
    """Facts access decisions are made from (the decisions live in handlers and the
    permission policy)."""

    @abc.abstractmethod
    def get_organization(
        self, admin_unit_id: ObjectId
    ) -> Optional[CurrentOrganizationReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_organizations(
        self, admin_unit_ids: Optional[List[ObjectId]]
    ) -> List[CurrentOrganizationReadModel]:  # pragma: no cover
        """`None` lists every organization by id; otherwise in the given order."""
        raise NotImplementedError

    @abc.abstractmethod
    def member_organization_ids(
        self, user_id: ObjectId
    ) -> List[ObjectId]:  # pragma: no cover
        """In membership order."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_resource_owner(
        self, kind: ResourceKind, resource_id: ObjectId
    ) -> Optional[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def has_other_admin(
        self, admin_unit_id: ObjectId, user_id: ObjectId
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_api_key_by_hash(
        self, key_hash: str
    ) -> Optional[ApiKeyReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def is_name_taken(
        self, name: str, exclude_id: Optional[ObjectId]
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def is_short_name_taken(
        self, short_name: str, exclude_id: Optional[ObjectId]
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def can_request_verification(
        self, source_admin_unit_id: ObjectId, target_admin_unit_id: ObjectId
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def any_accepts_reference_requests(
        self, exclude_admin_unit_id: ObjectId
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_settings(
        self, admin_unit_id: ObjectId
    ) -> Optional[OrganizationSettingsReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def count_incoming_badges(
        self, admin_unit_id: ObjectId
    ) -> ManageMenuOptionsReadModel:  # pragma: no cover
        """Inbox reference and verification requests addressed to the organization."""
        raise NotImplementedError

    @abc.abstractmethod
    def event_report_recipients(
        self, admin_unit_id: ObjectId, permission: str
    ) -> List[MailRecipientReadModel]:  # pragma: no cover
        """Users of members holding `permission` plus platform admins, by user id."""
        raise NotImplementedError
