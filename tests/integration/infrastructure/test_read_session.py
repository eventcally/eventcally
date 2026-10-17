"""The query-side read session: read-only, released per query, pool-safe."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import InternalError

from project.application.queries import Query
from project.application.query_bus import QueryBus
from project.infrastructure.query_handler_factory import QueryHandlerFactory
from project.infrastructure.read_session import SqlAlchemyReadSessionScope

READ_ONLY_SQL_TRANSACTION = "25006"


def _backend_pid(session_or_connection) -> int:
    return session_or_connection.execute(text("SELECT pg_backend_pid()")).scalar()


def _is_read_only(session_or_connection) -> bool:
    value = session_or_connection.execute(text("SHOW transaction_read_only")).scalar()
    return value == "on"


def _open_transactions_for(db, pid) -> int:
    with db.engine.connect() as connection:
        return connection.execute(
            text(
                "SELECT count(*) FROM pg_stat_activity"
                " WHERE pid = :pid AND state LIKE 'idle in transaction%'"
            ),
            {"pid": pid},
        ).scalar()


def test_write_through_read_session_fails(app, db):
    with app.app_context():
        read_session = app.container.infrastructure.read_session()

        with app.container.infrastructure.read_session_scope():
            assert _is_read_only(read_session)

            with pytest.raises(InternalError) as exc_info:
                read_session.execute(text("UPDATE settings SET tos = 'changed'"))

            assert exc_info.value.orig.pgcode == READ_ONLY_SQL_TRANSACTION


def test_read_only_flag_does_not_leak_into_pooled_connections(app, db):
    with app.app_context():
        read_session = app.container.infrastructure.read_session()

        with app.container.infrastructure.read_session_scope():
            read_pid = _backend_pid(read_session)
            assert _is_read_only(read_session)

        # Check out every pooled connection at once, so the one the read session
        # returned is among them, and none of them may still be read-only.
        pool = db.engine.pool
        connections = [db.engine.connect() for _ in range(max(pool.checkedin(), 1))]
        try:
            pids = [_backend_pid(connection) for connection in connections]
            assert read_pid in pids
            assert not any(_is_read_only(connection) for connection in connections)
        finally:
            for connection in connections:
                connection.close()

        # And the write session keeps working after a read scope. Postgres rejects
        # an UPDATE in a read-only transaction even if it matches no rows.
        assert not _is_read_only(db.session)
        db.session.execute(text("UPDATE settings SET tos = 'changed'"))
        db.session.commit()


def test_read_session_sees_committed_writes(app, db, seeder):
    user_id = seeder.create_user(email="reader@test.de")

    with app.app_context():
        read_session = app.container.infrastructure.read_session()

        with app.container.infrastructure.read_session_scope():
            email = read_session.execute(
                text('SELECT email FROM "user" WHERE id = :id'), {"id": user_id}
            ).scalar()

        assert email == "reader@test.de"


def test_scope_exit_releases_the_connection(app, db):
    with app.app_context():
        read_session = app.container.infrastructure.read_session()

        with app.container.infrastructure.read_session_scope():
            pid = _backend_pid(read_session)
            assert _open_transactions_for(db, pid) == 1
            assert read_session.registry.has()

        assert not read_session.registry.has()
        assert _open_transactions_for(db, pid) == 0


def test_scope_is_re_entrant(app, db):
    with app.app_context():
        read_session = app.container.infrastructure.read_session()
        scope = SqlAlchemyReadSessionScope(read_session)

        with scope:
            outer_session = read_session()
            outer_pid = _backend_pid(read_session)

            with scope:
                assert read_session() is outer_session
                assert _backend_pid(read_session) == outer_pid

            # The inner exit must not end the outer read transaction.
            assert read_session.registry.has()
            assert read_session() is outer_session

        assert not read_session.registry.has()


def test_scope_releases_the_connection_on_error(app, db):
    with app.app_context():
        read_session = app.container.infrastructure.read_session()

        with pytest.raises(RuntimeError):
            with app.container.infrastructure.read_session_scope():
                pid = _backend_pid(read_session)
                raise RuntimeError("boom")

        assert not read_session.registry.has()
        assert _open_transactions_for(db, pid) == 0


def test_read_session_is_scoped_per_app_context(app, db):
    with app.app_context():
        read_session = app.container.infrastructure.read_session()
        outer_session = read_session()

        with app.app_context():
            assert read_session() is not outer_session

        assert read_session() is outer_session
        read_session.remove()


def test_app_context_teardown_removes_read_session(app, db):
    read_session = app.container.infrastructure.read_session()

    with app.app_context():
        # A read outside any scope, as a legacy code path might do.
        pid = _backend_pid(read_session)
        assert read_session.registry.has()

    with app.app_context():
        assert _open_transactions_for(db, pid) == 0


def test_container_resolves_query_bus(app, db):
    with app.app_context():
        query_bus = app.container.cqrs.query_bus()

        assert isinstance(query_bus, QueryBus)
        assert isinstance(query_bus.query_handler_factory, QueryHandlerFactory)
        assert isinstance(query_bus.read_session_scope, SqlAlchemyReadSessionScope)
        assert (
            query_bus.read_session_scope.read_session
            is app.container.infrastructure.read_session()
        )

        # Scopes carry a depth counter, so they must not be shared between buses.
        assert app.container.cqrs.query_bus().read_session_scope is not (
            query_bus.read_session_scope
        )


class _CountUsersQuery(Query[int]):
    pass


class _CountUsersHandler:
    def __init__(self, read_session):
        self.read_session = read_session

    def handle(self, query):
        return self.read_session.execute(text('SELECT count(*) FROM "user"')).scalar()


def test_query_bus_runs_handler_on_read_session(app, db, seeder):
    seeder.create_user(email="counted@test.de")

    with app.app_context():
        infrastructure = app.container.infrastructure
        read_session = infrastructure.read_session()
        query_bus = QueryBus(
            app_context_provider=app.container.context.app_context_provider(),
            query_handler_factory=QueryHandlerFactory(
                lambda query_type: _CountUsersHandler(read_session)
            ),
            read_session_scope=infrastructure.read_session_scope(),
        )

        count = query_bus.handle(_CountUsersQuery())

        assert count >= 1
        assert not read_session.registry.has()
