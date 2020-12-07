def test_mail_server():
    import os

    os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/gsevpt_tests"
    os.environ["MAIL_SERVER"] = "mailserver.com"

    from project import app

    app.config["TESTING"] = True
    app.testing = True


def test_migrations(app):
    from flask_migrate import upgrade
    from project import db
    from project.init_data import create_initial_data

    with app.app_context():
        db.drop_all()
        db.engine.execute("DROP TABLE IF EXISTS alembic_version;")
        upgrade()
        create_initial_data()
