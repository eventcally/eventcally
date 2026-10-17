import abc
from typing import List, Optional

from project.application.queries.page_request import PageRequest
from project.application.read_models.page import Page
from project.application.read_models.user_admin_read_models import (
    NewsletterRecipientReadModel,
    RoleReadModel,
    UserAdminReadModel,
)
from project.domain.types.object_id import ObjectId


class AbstractUserAdminReadRepository(abc.ABC):
    @abc.abstractmethod
    def list_users(
        self, page_request: PageRequest
    ) -> Page[UserAdminReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_user(
        self, user_id: ObjectId
    ) -> Optional[UserAdminReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_roles(self) -> List[RoleReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_newsletter_recipients(
        self,
    ) -> List[NewsletterRecipientReadModel]:  # pragma: no cover
        raise NotImplementedError
