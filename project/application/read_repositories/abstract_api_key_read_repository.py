import abc
from typing import Optional, Union

from project.application.queries.list_organization_api_keys_query import (
    ListOrganizationApiKeysQuery,
)
from project.application.queries.list_user_api_keys_query import ListUserApiKeysQuery
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractApiKeyReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: Union[ListOrganizationApiKeysQuery, ListUserApiKeysQuery]
    ) -> Page[ApiKeyReadModel]:  # pragma: no cover
        """Keys of `query.admin_unit_id` or `query.user_id`."""
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, object_id: ObjectId) -> Optional[ApiKeyReadModel]:  # pragma: no cover
        raise NotImplementedError
