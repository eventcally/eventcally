import abc
from typing import Optional

from project.application.queries.list_user_oauth2_tokens_query import (
    ListUserOAuth2TokensQuery,
)
from project.application.read_models.oauth2_token_read_models import (
    OAuth2TokenReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractOAuth2TokenReadRepository(abc.ABC):
    @abc.abstractmethod
    def list(
        self, query: ListUserOAuth2TokensQuery
    ) -> Page[OAuth2TokenReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[OAuth2TokenReadModel]:  # pragma: no cover
        raise NotImplementedError
