import sqlalchemy


def test_mail_server():
    import os

    os.environ["MAIL_SERVER"] = "mailserver.com"

    from project import app

    app.config["TESTING"] = True
    app.testing = True


def drop_db(db):
    db.drop_all()
    db.engine.execute("DROP TABLE IF EXISTS alembic_version;")


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
    db.engine.execute(sqlalchemy.text(sql).execution_options(autocommit=True))


def test_migrations(app, seeder):
    from flask_migrate import downgrade, upgrade

    from project import db
    from project.init_data import create_initial_data

    with app.app_context():
        drop_db(db)
        upgrade()
        create_initial_data()
        user_id, admin_unit_id = seeder.setup_base()
        seeder.upsert_default_event_place(admin_unit_id)
        seeder.upsert_default_event_organizer(admin_unit_id)
        event_id = seeder.create_event(admin_unit_id)
        seeder.upsert_default_image()
        seeder.create_event_suggestion(admin_unit_id)
        seeder.create_any_reference(admin_unit_id)
        seeder.create_reference_request(event_id, admin_unit_id)
        downgrade()


def test_migration_public_status(app, seeder):
    from flask_migrate import upgrade

    from project import db
    from project.models import Event, PublicStatus

    with app.app_context():
        drop_db(db)
        upgrade(revision="1fb9f679defb")
        populate_db(db)
        upgrade()

        events = Event.query.all()
        assert len(events) > 0

        for event in events:
            assert event.public_status == PublicStatus.published


def test_migration_event_definitions(app, seeder):
    from flask_migrate import upgrade

    from project import db
    from project.models import Event

    with app.app_context():
        drop_db(db)
        upgrade(revision="920329927dc6")
        populate_db(db)
        upgrade()

        events = Event.query.all()
        assert len(events) > 0

        for event in events:
            assert len(event.date_definitions) == 1
