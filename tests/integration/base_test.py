import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


class BaseTest:
    seeder: Seeder = None
    utils: UtilActions = None
    client = None
    app = None
    db = None

    @pytest.fixture(autouse=True)
    def _inject_fixtures(self, client, seeder, utils, app, db):
        self.client = client
        self.seeder = seeder
        self.utils = utils
        self.app = app
        self.db = db

        self.setup_with_fixtures()

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        pass

    def setup_method(self):
        pass

    def teardown_method(self):
        pass

    def setup_with_fixtures(self):
        pass
