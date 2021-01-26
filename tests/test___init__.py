def test_mail_server():
    import os

    os.environ["MAIL_SERVER"] = "mailserver.com"

    from project import app

    app.config["TESTING"] = True
    app.testing = True


def test_migrations(app, seeder):
    from flask_migrate import upgrade, downgrade
    from project import db
    from project.init_data import create_initial_data

    with app.app_context():
        db.drop_all()
        db.engine.execute("DROP TABLE IF EXISTS alembic_version;")
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
