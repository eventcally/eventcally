from typing import Optional

from sqlalchemy import select

from project.application.queries.list_user_oauth2_tokens_query import (
    ListUserOAuth2TokensQuery,
)
from project.application.read_models.oauth2_token_read_models import (
    OAuth2TokenReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_oauth2_token_read_repository import (
    AbstractOAuth2TokenReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import OAuth2Client, OAuth2Token
from project.infrastructure.read_repositories.query_helpers import paginate


def _select():
    return select(OAuth2Token, OAuth2Client).outerjoin(
        OAuth2Client, OAuth2Client.client_id == OAuth2Token.client_id
    )


class SqlAlchemyOAuth2TokenReadRepository(AbstractOAuth2TokenReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def list(self, query: ListUserOAuth2TokensQuery) -> Page[OAuth2TokenReadModel]:
        filters = [OAuth2Token.user_id == query.user_id]
        stmt = (
            _select()
            .where(*filters)
            .order_by(OAuth2Token.issued_at.desc(), OAuth2Token.id)
        )
        count_stmt = select(OAuth2Token.id).where(*filters)
        return paginate(self.session, stmt, count_stmt, query.page, _to_model)

    def get(self, object_id: ObjectId) -> Optional[OAuth2TokenReadModel]:
        row = self.session.execute(
            _select().where(OAuth2Token.id == object_id)
        ).one_or_none()
        return _to_model(row) if row else None


def _to_model(row) -> OAuth2TokenReadModel:
    token, client = row

    return OAuth2TokenReadModel(
        id=token.id,
        user_id=token.user_id,
        client_name=client.client_name if client else None,
        scope=token.scope,
        issued_at=token.issued_at,
        expires_in=token.expires_in or 0,
        access_token_revoked_at=token.access_token_revoked_at or 0,
        refresh_token_revoked_at=token.refresh_token_revoked_at or 0,
    )
