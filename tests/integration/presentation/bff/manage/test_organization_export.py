import pytest
from dependency_injector import providers

from project.application.read_models.organization_export_read_models import (
    OrganizationExportJobStatusReadModel,
)
from project.application.services.abstract_organization_export_dispatcher import (
    AbstractOrganizationExportDispatcher,
)
from project.application.services.abstract_organization_export_reader import (
    AbstractOrganizationExportReader,
)
from project.application.services.organization_export_jobs import (
    new_organization_export_job_id,
)
from project.infrastructure.services import file_system_organization_export_reader
from project.presentation.web.views import manage

EXPORT_URL = "/bff/manage/organizations/{}/export"
JOB_URL = "/bff/manage/organizations/{}/export/jobs/{}"


class _Dispatcher(AbstractOrganizationExportDispatcher):
    def __init__(self, tracked=True):
        self.tracked = tracked
        self.calls = []

    def start(self, admin_unit_id, job_id):
        self.calls.append((admin_unit_id, job_id))
        return self.tracked


class _Reader(AbstractOrganizationExportReader):
    def get_file(self, admin_unit_id):  # pragma: no cover
        raise NotImplementedError

    def get_job_status(self, job_id):
        return OrganizationExportJobStatusReadModel(
            job_id=job_id, ready=True, successful=False
        )


@pytest.fixture
def dump_dir(tmp_path, mocker):
    mocker.patch.object(
        file_system_organization_export_reader, "dump_org_path", str(tmp_path)
    )
    mocker.patch.object(manage, "dump_org_path", str(tmp_path))
    return tmp_path


@pytest.fixture
def dispatcher(app):
    fake = _Dispatcher()
    app.container.services.organization_export_dispatcher.override(
        providers.Object(fake)
    )
    yield fake
    app.container.services.organization_export_dispatcher.reset_override()


@pytest.fixture
def reader(app):
    app.container.services.organization_export_reader.override(
        providers.Object(_Reader())
    )
    yield
    app.container.services.organization_export_reader.reset_override()


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/export")


def _foreign_admin_unit(seeder):
    owner_id = seeder.create_user(email="other@test.de")
    return seeder.create_admin_unit(owner_id, name="Andere Crew")


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    job_id = new_organization_export_job_id(admin_unit_id)

    assert utils.get_json(EXPORT_URL.format(admin_unit_id)).status_code == 401
    assert utils.post_json(EXPORT_URL.format(admin_unit_id), {}).status_code == 401
    assert utils.get_json(JOB_URL.format(admin_unit_id, job_id)).status_code == 401


def test_foreign_organization_is_403(client, seeder, utils, dispatcher):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    other_id = _foreign_admin_unit(seeder)
    job_id = new_organization_export_job_id(other_id)

    assert utils.get_json(EXPORT_URL.format(other_id)).status_code == 403
    assert utils.post_json(EXPORT_URL.format(other_id), {}).status_code == 403
    assert utils.get_json(JOB_URL.format(other_id, job_id)).status_code == 403
    assert dispatcher.calls == []


def test_unknown_organization_is_403(client, seeder, utils, dispatcher):
    seeder.setup_base()

    assert utils.get_json(EXPORT_URL.format(4711)).status_code == 403


def test_start_requires_csrf(client, seeder, utils, dispatcher):
    _, admin_unit_id = seeder.setup_base()

    assert utils.post_json(EXPORT_URL.format(admin_unit_id), {}).status_code == 400
    assert dispatcher.calls == []


# get


def test_get_without_file(client, seeder, utils, dump_dir):
    _, admin_unit_id = seeder.setup_base()

    assert utils.get_json_ok(EXPORT_URL.format(admin_unit_id)).json == {"file": None}


def test_get_with_file_and_download(client, seeder, utils, dump_dir):
    _, admin_unit_id = seeder.setup_base()
    (dump_dir / f"org-{admin_unit_id}.zip").write_bytes(b"x" * 42)

    file = utils.get_json_ok(EXPORT_URL.format(admin_unit_id)).json["file"]

    assert file["size"] == 42
    assert file["created_at"]
    assert file["url"] == (
        f"/manage/admin_unit/{admin_unit_id}/export/dump/org-{admin_unit_id}.zip"
    )
    assert utils.get_ok(file["url"]).data == b"x" * 42


# start


def test_start(client, seeder, utils, dispatcher):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)

    body = utils.post_json(EXPORT_URL.format(admin_unit_id), {}).json

    assert dispatcher.calls == [(admin_unit_id, body["job_id"])]
    assert body["job_id"].startswith(f"org-export-{admin_unit_id}-")


def test_start_eager_has_no_job(client, seeder, utils, dispatcher):
    _, admin_unit_id = seeder.setup_base()
    _shell(utils, admin_unit_id)
    dispatcher.tracked = False

    body = utils.post_json(EXPORT_URL.format(admin_unit_id), {}).json

    assert body == {"job_id": None}


# job status


def test_job_status(client, seeder, utils, reader):
    _, admin_unit_id = seeder.setup_base()
    job_id = new_organization_export_job_id(admin_unit_id)

    body = utils.get_json_ok(JOB_URL.format(admin_unit_id, job_id)).json

    assert body == {"ready": True, "successful": False}


def test_job_of_another_organization_is_404(client, seeder, utils, reader):
    _, admin_unit_id = seeder.setup_base()
    job_id = new_organization_export_job_id(admin_unit_id + 1)

    utils.assert_response_notFound(
        utils.get_json(JOB_URL.format(admin_unit_id, job_id))
    )


def test_garbage_job_id_is_404(client, seeder, utils, reader):
    _, admin_unit_id = seeder.setup_base()

    utils.assert_response_notFound(
        utils.get_json(JOB_URL.format(admin_unit_id, "garbage"))
    )
