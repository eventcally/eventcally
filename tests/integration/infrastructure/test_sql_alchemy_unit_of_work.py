import pytest
from sqlalchemy.exc import SQLAlchemyError

from project.domain.errors import InfrastructureError
from project.infrastructure.extensions import db
from project.infrastructure.sql_alchemy_unit_of_work import SqlAlchemyUnitOfWork


def test_commit_error_rolls_back_and_raises_a_domain_error(app, mocker):
    with app.app_context():
        uow = SqlAlchemyUnitOfWork(db.session)
        mocker.patch.object(uow.session, "commit", side_effect=SQLAlchemyError("boom"))
        rollback = mocker.patch.object(uow.session, "rollback")

        with pytest.raises(InfrastructureError):
            uow.commit()

        rollback.assert_called_once_with()


def test_rollback_rolls_the_session_back(app, mocker):
    with app.app_context():
        uow = SqlAlchemyUnitOfWork(db.session)
        rollback = mocker.patch.object(uow.session, "rollback")

        uow.rollback()

        rollback.assert_called_once_with()
