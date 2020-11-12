import pytest
from project import app, db

@pytest.fixture
def client():
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres@localhost/gsevpt_tests"
    app.config["TESTING"] = True
    app.testing = True

    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield client