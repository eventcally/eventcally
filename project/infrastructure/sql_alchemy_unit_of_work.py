from __future__ import annotations

from psycopg2.errorcodes import CHECK_VIOLATION, UNIQUE_VIOLATION
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import Session

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import ConstraintError, DuplicateError, InfrastructureError
from project.infrastructure.repositories import (
    SqlAlchemyEventOrganizerRepository,
    SqlAlchemyEventPlaceRepository,
    SqlAlchemyOrganizationRepository,
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, scoped_session_or_factory):
        if isinstance(scoped_session_or_factory, scoped_session):
            self.session_factory = scoped_session_or_factory
            self.is_scoped = True
        else:  # pragma: no cover
            self.session_factory = scoped_session_or_factory
            self.is_scoped = False

        self.session: Session = (
            self.session_factory() if not self.is_scoped else self.session_factory
        )
        self.event_organizers = SqlAlchemyEventOrganizerRepository(self.session)
        self.event_places = SqlAlchemyEventPlaceRepository(self.session)
        self.organizations = SqlAlchemyOrganizationRepository(self.session)

    def __exit__(self, exc_type, exc, traceback) -> bool:
        super().__exit__(exc_type, exc, traceback)
        if not self.is_scoped:  # pragma: no cover
            self.session.close()

        if isinstance(exc, SQLAlchemyError):
            self._reraiseSqlErrorMessage(exc)

        return False  # propagate domain errors

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def _reraiseSqlErrorMessage(self, e: SQLAlchemyError):
        if hasattr(e.orig, "pgcode"):
            if e.orig.pgcode == UNIQUE_VIOLATION:
                raise DuplicateError(cause=e)

            if e.orig.pgcode == CHECK_VIOLATION:  # pragma: no cover
                raise ConstraintError(cause=e)

        raise InfrastructureError(cause=e)
