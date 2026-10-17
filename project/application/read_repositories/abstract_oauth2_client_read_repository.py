import abc
from typing import Optional, Union

from project.application.queries.list_apps_query import ListAppsQuery
from project.application.queries.list_organization_oauth2_clients_query import (
    ListOrganizationOAuth2ClientsQuery,
)
from project.application.queries.list_user_oauth2_clients_query import (
    ListUserOAuth2ClientsQuery,
)
from project.application.read_models.oauth2_client_read_models import (
    AppReadModel,
    OAuth2ClientReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOAuth2ClientReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self,
        query: Union[
            ListOrganizationOAuth2ClientsQuery,
            ListUserOAuth2ClientsQuery,
            ListAppsQuery,
        ],
    ) -> Page[OAuth2ClientReadModel]:  # pragma: no cover
        """Apps for `ListAppsQuery`, otherwise plain clients of the owner."""
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OAuth2ClientReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_app(
        self, object_id: ObjectId
    ) -> Optional[AppReadModel]:  # pragma: no cover
        raise NotImplementedError
