from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.oauth2_token_aggregate import OAuth2TokenAggregate


def ensure_oauth2_token_exists(
    oauth2_token_id: int, uow: AbstractUnitOfWork
) -> OAuth2TokenAggregate:
    oauth2_token = uow.oauth2_tokens.get(oauth2_token_id)

    if not oauth2_token:
        raise NotFoundError(f"OAuth2 token with id {oauth2_token_id} not found")

    return oauth2_token
