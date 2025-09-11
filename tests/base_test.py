import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


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


class BaseTestView(BaseTest):
    endpoint_name: str = None
    model: type = None

    def _get_endpoint_kwargs(self) -> dict:
        return dict()

    def _insert_default_object(self) -> int:
        raise NotImplementedError()


class BaseTestObjectView(BaseTestView):
    object_id: int = None
    endpoint_object_id_arg_name: str = None

    def _get_endpoint_kwargs(self) -> dict:
        result = super()._get_endpoint_kwargs()
        result[self.endpoint_object_id_arg_name] = self.object_id
        return result

    def _setup_default_object(self):
        self.object_id = self._insert_default_object()

    def _get_object(self):
        return self.db.session.get(self.model, self.object_id)


class BaseTestCreateView(BaseTestObjectView):
    def test(self):
        # GET
        endpoint_kwargs = self._get_endpoint_kwargs()
        url = self.utils.get_url(self.endpoint_name, **endpoint_kwargs)
        response = self.utils.get_ok(url)

        # POST
        form_values = dict()
        self._fill_form_values(form_values)
        response = self.utils.post_form(
            url,
            response,
            form_values,
        )
        self.utils.assert_status_code(response, 302)

        # Check object after submit
        with self.app.app_context():
            object = self.model.query.order_by(self.model.id.desc()).first()
            self.object_id = object.id
            self._check_object_after_submit(object)

    def _fill_form_values(self, values: dict):
        pass

    def _check_object_after_submit(self, object):
        assert object is not None


class BaseTestReadView(BaseTestObjectView):
    def test(self):
        self._setup_default_object()
        endpoint_kwargs = self._get_endpoint_kwargs()
        self.utils.get_endpoint_ok(self.endpoint_name, **endpoint_kwargs)


class BaseTestUpdateView(BaseTestObjectView):
    def test(self):
        self._setup_default_object()

        # GET
        endpoint_kwargs = self._get_endpoint_kwargs()
        url = self.utils.get_url(self.endpoint_name, **endpoint_kwargs)
        response = self.utils.get_ok(url)

        # POST
        form_values = dict()
        with self.app.app_context():
            object = self._get_object()
            self._fill_form_values(form_values, object)

        response = self.utils.post_form(
            url,
            response,
            form_values,
        )
        self.utils.assert_status_code(response, 302)

        # Check object after submit
        with self.app.app_context():
            object = self._get_object()
            self._check_object_after_submit(object)

    def _fill_form_values(self, values: dict, object):
        pass

    def _check_object_after_submit(self, object):
        assert object is not None


class BaseTestDeleteView(BaseTestObjectView):
    def test(self):
        self._setup_default_object()

        # GET
        endpoint_kwargs = self._get_endpoint_kwargs()
        url = self.utils.get_url(self.endpoint_name, **endpoint_kwargs)
        response = self.utils.get_ok(url)

        # POST
        form_values = dict()
        with self.app.app_context():
            object = self._get_object()
            self._fill_form_values(form_values, object)

        response = self.utils.post_form(
            url,
            response,
            form_values,
        )
        self.utils.assert_status_code(response, 302)

        # Check object after submit
        with self.app.app_context():
            object = self._get_object()
            self._check_object_after_submit(object)

    def _fill_form_values(self, values: dict, object):
        pass

    def _check_object_after_submit(self, object):
        assert object is None


class BaseTestListView(BaseTestView):
    def test(self):
        self._insert_default_object()
        endpoint_kwargs = self._get_endpoint_kwargs()
        self.utils.get_endpoint_ok(self.endpoint_name, **endpoint_kwargs)
