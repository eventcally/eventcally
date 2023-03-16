import os
import warnings

import pytest
from sqlalchemy.exc import SAWarning

from .seeder import Seeder
from .utils import UtilActions


def pytest_generate_tests(metafunc):
    warnings.filterwarnings("error", category=SAWarning)

    os.environ["DATABASE_URL"] = os.environ.get(
        "TEST_DATABASE_URL", "postgresql://postgres@localhost/gsevpt_tests"
    )
    os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"
    os.environ[
        "JWT_PRIVATE_KEY"
    ] = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAvy41pD9VTDVmGVxkeSPUDGuzULf0rfVFypnVnBO12l0V/fXU\n0Rdqf9qlSCklwSWFT7XcGRS9gDw/HGkbQ2qycmQ0+S2FbU65D3VKR1amqtMgonDF\nwNinoCEBfh6H52RpvduKmdMZ3PfhqTZP5rStxs7uHuAa+BBzqCl4fTBcwB+sDM+l\nE5tPuGkoXCZAEllw7G5lHKETZJt2dsvf0aBlPSb+pITQkLLSC1OjbAHmo3h7PP1y\nQU0qnHsCJv7BhGIFTy3cfvbsa1QdNxI3VHg7ZP2vs+JFm4cDxdk+nft8dDnP8z42\nkha0iqiLAWDLOyyk+kP7EHvn0jgpZM6N6tzJxwIDAQABAoIBAA5vGrWv4mzCi1bW\n1u8eeWAGsZ8ihGKt5fsJ6krCYjR+Wq615L90mSHWDCyKjsMqZgpCnL94BWatJcar\nWNeaMqbYUfeOLEi4bNhx7o28SREUp54cDZIlyWIZm9c9ztz1g9ZFwQ0kFwvL20m/\nRAETGxure+bw3JhmBZVorCQnhpkqqY68od+vmgprYXSZjXV0oyJGnlml2RzZW9b1\nDLP45lPv2AHdoXiNVBWDf6AXFDAXVEo3O6O9Uyn1TuEfF8DK0wbTvAA+3xGHQ5ad\nXsGq+a22Y2nBqHFjCYVCx8hu5meHJdOAy4ckCSt44cC3WKsdoqKFQW9oOp9SUHyE\nYEABqmECgYEA5xYcD+Y9itTU3jjUb+PpU2B23x6EXcrg8ubOLTaLHi3LK07CTnp0\nLd1jNmmmaaXNbpHHMXDTvDQg74y17Z5mvHey3oF3F7WMGxOz5EGl51+InThegd2c\n/vDEw9FCdr8VGDmHh4VkwwgD+KeV+R0q78ik9V1I+0EKZb03h5mvI70CgYEA08q2\n3MQofjazVsNYVESuK6z9FCezBVg0Ko5/D3l5UtAgOeUXzovbEHm0jsOCy3gAgEZz\nakIKj8OX6Hc1HzwluBi8CSqsXHM6miahTl0HIoYtnYwD9hSnb8+vBOCohrhf1gKh\n1OzY1ZjjNwCJ+RqThMJJWKdRCLxiIhXZ1KD2edMCgYAJHH4Owm06xBmAiY0WvE2+\n09bcBUAC0rT73s3SSoxBrFyOYJSYs4tRI6F9y7yb/cWTznukH2a5zPRffZTOwagb\nVjzfOQuRC79ycdxt64i3DrU8PbS8OhiulJ+teNq+A9q5EcueNEw8xFwjubfYEqZW\nvfqDEiKGhZH7YPKHji+xoQKBgHRhh5zG2e2JR4Fc9PPRjdgIRkXGDvTX5EqiZSXu\nvYGJRrwprKxeY/Gov1RYEU6X0carcA6q3bzkYVxn7TQNzDhety1eWrquwzwkEC3M\npvgMvZI+d4rJDL0/ZdCLV3A4bsleRumHgRvW2LzHugm91eR1EvL5dmkTg+VxFnNm\nRCrrAoGBAKgTNyhkQwHNWCgXg/9gHZcbigp6r8l8SS/Ph3yV53iSN99GUW5AZhE8\nzaLjKVoQQJDQZNpu1ZFEKmSH3UNMERYrYhdim2hcELmlPL/8cDJ185gApEaTS27M\nH9kWWtKDwB5So8k2Nragqk/RUp4u54L8L7IHzLtdo4y6s5ohO0+k\n-----END RSA PRIVATE KEY-----\n"
    os.environ[
        "JWT_PUBLIC_JWKS"
    ] = '{"keys":[{"kid":"default","kty":"RSA","use":"sig","alg":"RS256","n":"vy41pD9VTDVmGVxkeSPUDGuzULf0rfVFypnVnBO12l0V_fXU0Rdqf9qlSCklwSWFT7XcGRS9gDw_HGkbQ2qycmQ0-S2FbU65D3VKR1amqtMgonDFwNinoCEBfh6H52RpvduKmdMZ3PfhqTZP5rStxs7uHuAa-BBzqCl4fTBcwB-sDM-lE5tPuGkoXCZAEllw7G5lHKETZJt2dsvf0aBlPSb-pITQkLLSC1OjbAHmo3h7PP1yQU0qnHsCJv7BhGIFTy3cfvbsa1QdNxI3VHg7ZP2vs-JFm4cDxdk-nft8dDnP8z42kha0iqiLAWDLOyyk-kP7EHvn0jgpZM6N6tzJxw","e":"AQAB"}]}'
    os.environ["GOOGLE_MAPS_API_KEY"] = "AIzaDummy"
    os.environ["TESTING"] = "1"


@pytest.fixture
def app():
    from project import app

    app.config["SERVER_NAME"] = None
    app.config["TESTING"] = True
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = False
    app.testing = True

    return app


@pytest.fixture
def db(app):
    from flask_migrate import stamp

    from project import db
    from project.init_data import create_initial_data

    with app.app_context():
        db.drop_all()
        db.create_all()
        stamp()
        create_initial_data()

    return db


@pytest.fixture
def client(app, db):
    return app.test_client()


@pytest.fixture
def utils(client, app, mocker, requests_mock):
    return UtilActions(client, app, mocker, requests_mock)


@pytest.fixture
def seeder(app, db, utils):
    return Seeder(app, db, utils)
