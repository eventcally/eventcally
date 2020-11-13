import pytest
import os

def pytest_generate_tests(metafunc):
    os.environ["DATABASE_URL"] = "postgresql://postgres@localhost/gsevpt_tests"

@pytest.fixture
def client():
    from project import app, db
    app.config["TESTING"] = True
    app.testing = True

    client = app.test_client()
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield client