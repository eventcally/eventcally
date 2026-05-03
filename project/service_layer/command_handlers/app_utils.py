from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.models.oauth import OAuth2Client


def ensure_app_exists(app_id: int, uow: AbstractUnitOfWork) -> OAuth2Client:
    app = uow.apps.get(app_id)

    if not app:
        raise NotFoundError(f"App with id {app_id} not found")

    return app
