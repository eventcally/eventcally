import pytest
import os
from .utils import UtilActions


def pytest_generate_tests(metafunc):
    os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/gsevpt_tests"


@pytest.fixture
def app():
    from project import app

    app.config["TESTING"] = True
    app.testing = True

    return app


@pytest.fixture
def db(app):
    from project import db

    with app.app_context():
        db.drop_all()
        db.create_all()

    return db


@pytest.fixture
def client(app, db):
    return app.test_client()


@pytest.fixture
def utils(client):
    return UtilActions(client)
