from __future__ import annotations

from flask.globals import app_ctx
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from project.application.abstract_read_session_scope import AbstractReadSessionScope

READONLY_EXECUTION_OPTIONS = {"postgresql_readonly": True}


def _app_ctx_id() -> int:
    """Scope read sessions to the Flask app context, as Flask-SQLAlchemy 3 does."""
    return id(app_ctx._get_current_object())


class ReadOnlySession(Session):
    """Session bound lazily to a read-only view of the app's engine.

    The engine is resolved on first use, so the session can be created outside an
    app context. `postgresql_readonly` makes the database reject any write.
    """

    def __init__(self, db, **kwargs):
        self._db = db
        self._readonly_engine = None
        super().__init__(**kwargs)

    def get_bind(self, mapper=None, clause=None, **kwargs) -> Engine:
        if self._readonly_engine is None:
            self._readonly_engine = self._db.engine.execution_options(
                **READONLY_EXECUTION_OPTIONS
            )

        return self._readonly_engine


def create_read_session(db) -> scoped_session:
    return scoped_session(
        sessionmaker(
            class_=ReadOnlySession,
            db=db,
            autoflush=False,
            expire_on_commit=False,
        ),
        scopefunc=_app_ctx_id,
    )


class SqlAlchemyReadSessionScope(AbstractReadSessionScope):
    """Re-entrant scope; the outermost exit removes the read session.

    `remove()` rolls back the read-only transaction and returns the connection to
    the pool, so no read transaction outlives a top-level query.
    """

    def __init__(self, read_session: scoped_session):
        self.read_session = read_session
        self.depth = 0

    def __enter__(self) -> SqlAlchemyReadSessionScope:
        self.depth += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.depth -= 1

        if self.depth == 0:
            self.read_session.remove()
