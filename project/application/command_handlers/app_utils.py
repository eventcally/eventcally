from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.app_aggregate import AppAggregate
from project.domain.types import ObjectId


def ensure_app_exists(app_id: int, uow: AbstractUnitOfWork) -> AppAggregate:
    app = uow.apps.get(app_id)

    if not app:
        raise NotFoundError(f"App with id {app_id} not found")

    return app


def ensure_app_belongs_to_admin_unit(app: AppAggregate, admin_unit_id: ObjectId):
    """Guard against a command that pairs an admin unit the actor is permitted
    for with an app owned by a different one — a permission check on the admin
    unit alone would otherwise let the command act on the foreign app."""
    if app.admin_unit_id != admin_unit_id:
        raise UnauthorizedError(
            f"App {app.id} does not belong to admin unit {admin_unit_id}."
        )
