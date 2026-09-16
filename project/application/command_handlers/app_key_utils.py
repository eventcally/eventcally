from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.app_key_aggregate import AppKeyAggregate


def ensure_app_key_exists(id: int, uow: AbstractUnitOfWork) -> AppKeyAggregate:
    app_key = uow.app_keys.get(id)

    if not app_key:  # pragma: no cover
        raise NotFoundError(f"App key with id {id} not found")

    return app_key
