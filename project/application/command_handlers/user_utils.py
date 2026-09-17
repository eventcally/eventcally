from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.user_aggregate import UserAggregate


def ensure_user_exists(user_id: int, uow: AbstractUnitOfWork) -> UserAggregate:
    user = uow.users.get(user_id)

    if not user:  # pragma: no cover
        raise NotFoundError(f"User with id {user_id} not found")

    return user
