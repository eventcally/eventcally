from __future__ import annotations

from typing import NoReturn

from psycopg2.errorcodes import CHECK_VIOLATION, UNIQUE_VIOLATION
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from project.domain.errors import ConstraintError, DuplicateError, InfrastructureError


def raise_domain_error_from_sql_error(e: SQLAlchemyError) -> NoReturn:
    if hasattr(e, "orig") and hasattr(e.orig, "pgcode"):
        if e.orig.pgcode == UNIQUE_VIOLATION:
            raise DuplicateError(cause=e)

        if e.orig.pgcode == CHECK_VIOLATION:
            raise ConstraintError(cause=e)

    raise InfrastructureError(cause=e)


def flush(session: Session):
    try:
        session.flush()
    except SQLAlchemyError as e:
        raise_domain_error_from_sql_error(e)
