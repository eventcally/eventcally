import logging

import pytest
import sqlalchemy


def test_mail_server(monkeypatch):
    monkeypatch.setenv("MAIL_SERVER", "mailserver.com")

    from project.factory import create_app

    app = create_app({"TESTING": True})
    app.testing = True


def test_log_message_called_via_email_dispatched_signal(app, caplog):
    """Covers the log_message function body registered by the factory."""
    from unittest.mock import MagicMock

    from flask_mail import email_dispatched

    # The log_message function is registered when MAIL_SUPPRESS_SEND=True (always in tests).
    # Emit the signal manually to exercise the inner function.
    msg = MagicMock()
    msg.subject = "Test Subject"
    msg.body = "Test Body"
    msg.recipients = ["a@test.de"]

    with app.app_context(), caplog.at_level(logging.INFO, logger="project.factory"):
        email_dispatched.send(app, message=msg)

    record = next(r for r in caplog.records if r.getMessage().startswith("Mail not"))
    assert record.recipients == ["a@test.de"]
    assert record.subject == "Test Subject"
    assert record.body == "Test Body"


def _remote_address(config_override, forwarded_for=None):
    from flask_limiter.util import get_remote_address

    from project.factory import create_app

    app = create_app({"TESTING": True, **config_override})
    app.add_url_rule("/remote-address", "remote_address", get_remote_address)

    headers = {"X-Forwarded-For": forwarded_for} if forwarded_for else {}
    return app.test_client().get("/remote-address", headers=headers).text


def test_proxy_fix_disabled_by_default():
    assert _remote_address({}, "203.0.113.7, 172.24.0.1") == "127.0.0.1"


def test_proxy_fix_from_env(monkeypatch):
    monkeypatch.setenv("PROXY_FIX_X_FOR", "1")

    assert _remote_address({}, "203.0.113.7, 172.24.0.1") == "172.24.0.1"


@pytest.mark.parametrize(
    "forwarded_for, expected",
    [
        ("203.0.113.7, 172.24.0.1", "203.0.113.7"),
        ("198.51.100.1, 203.0.113.7, 172.24.0.1", "203.0.113.7"),
        ("172.24.0.1", "127.0.0.1"),
        (None, "127.0.0.1"),
    ],
)
def test_proxy_fix_behind_two_proxies(forwarded_for, expected):
    assert _remote_address({"PROXY_FIX_X_FOR": 2}, forwarded_for) == expected


def drop_db(db):
    from tests.integration.conftest import force_drop_all

    with db.engine.connect() as conn:
        with conn.begin():
            force_drop_all(db)
            conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS alembic_version;"))
            conn.execute(sqlalchemy.text("DROP TABLE IF EXISTS analytics;"))


def populate_db(db):
    sql = """
DO $$
DECLARE
    admin_unit_id adminunit.id%TYPE;
    event_place_id eventplace.id%TYPE;
    organizer_id eventorganizer.id%TYPE;
    event_id event.id%TYPE;
BEGIN
    INSERT INTO adminunit (name) VALUES ('Org') RETURNING id INTO admin_unit_id;
    INSERT INTO eventplace (name, admin_unit_id) VALUES ('Place', admin_unit_id) RETURNING id INTO event_place_id;
    INSERT INTO eventorganizer (name, admin_unit_id) VALUES ('Organizer', admin_unit_id) RETURNING id INTO organizer_id;
    INSERT INTO event (name, admin_unit_id, event_place_id, organizer_id, start) VALUES ('Event', admin_unit_id, event_place_id, organizer_id, current_timestamp) RETURNING id INTO event_id;
END $$;
        """
    with db.engine.connect() as conn:
        with conn.begin():
            conn.execute(sqlalchemy.text(sql).execution_options(autocommit=True))


def migrate_with_result(app):
    from alembic import command

    config = app.extensions["migrate"].migrate.get_config(
        None, opts=["autogenerate"], x_arg=None
    )
    return command.revision(
        config,
        None,
        autogenerate=True,
        sql=False,
        head="head",
        splice=False,
        branch_label=None,
        version_path=None,
        rev_id=None,
    )


def test_migrations(app, seeder):
    from flask_migrate import downgrade, upgrade

    from project.infrastructure.extensions import db
    from project.infrastructure.init_data import create_initial_data

    with app.app_context():
        drop_db(db)
        upgrade()
        migrate_result = migrate_with_result(app)
        assert not migrate_result
        create_initial_data()
        user_id, admin_unit_id = seeder.setup_base()
        seeder.upsert_default_event_place(admin_unit_id)
        seeder.upsert_default_event_organizer(admin_unit_id)
        event_id = seeder.create_event(admin_unit_id)
        seeder.upsert_default_image()
        seeder.create_any_reference(admin_unit_id)
        seeder.create_reference_request(event_id, admin_unit_id)
        db.session.commit()
        downgrade()


def test_migration_public_status(app, seeder):
    from flask_migrate import upgrade

    from project.infrastructure.extensions import db
    from project.infrastructure.models import Event, EventPublicStatus

    with app.app_context():
        drop_db(db)
        upgrade(revision="1fb9f679defb")
        populate_db(db)
        upgrade()

        events = Event.query.all()
        assert len(events) > 0

        for event in events:
            assert event.public_status == EventPublicStatus.published


def test_migration_event_definitions(app, seeder):
    from flask_migrate import upgrade

    from project.infrastructure.extensions import db
    from project.infrastructure.models import Event

    with app.app_context():
        drop_db(db)
        upgrade(revision="920329927dc6")
        populate_db(db)
        upgrade()

        events = Event.query.all()
        assert len(events) > 0

        for event in events:
            assert len(event.date_definitions) == 1


def test_common_scenario(app, seeder):
    seeder.create_common_scenario()
