import pytest

from project.application import queries
from project.application.query_handlers import GetOrganizationExportJobStatusHandler
from project.application.read_models.organization_export_read_models import (
    OrganizationExportJobStatusReadModel,
)
from project.application.services.abstract_organization_export_reader import (
    AbstractOrganizationExportReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.organization_export_jobs import (
    new_organization_export_job_id,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader


class FakeExportReader(AbstractOrganizationExportReader):
    def __init__(self):
        self.calls = []

    def get_file(self, admin_unit_id):  # pragma: no cover
        raise NotImplementedError

    def get_job_status(self, job_id):
        self.calls.append(job_id)
        return OrganizationExportJobStatusReadModel(
            job_id=job_id, ready=True, successful=True
        )


def _handle(actor, job_id, reader):
    handler = GetOrganizationExportJobStatusHandler(
        reader,
        ActorAuthorizationService(FakeReader(members=[(5, 7, "export:read")])),
    )
    return handler.handle(
        queries.GetOrganizationExportJobStatusQuery(
            actor=actor, admin_unit_id=5, job_id=job_id
        )
    )


def test_member_reads_status_of_own_job():
    job_id = new_organization_export_job_id(5)

    status = _handle(Actor(user_id=7), job_id, FakeExportReader())

    assert status.job_id == job_id
    assert status.successful is True


@pytest.mark.parametrize(
    "job_id", [new_organization_export_job_id(6), "garbage", "org-export-5-nope"]
)
def test_foreign_or_invalid_job_is_none_without_lookup(job_id):
    reader = FakeExportReader()

    assert _handle(Actor(user_id=7), job_id, reader) is None
    assert reader.calls == []


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
def test_others_are_unauthorized_before_lookup(actor):
    reader = FakeExportReader()

    with pytest.raises(UnauthorizedError):
        _handle(actor, new_organization_export_job_id(5), reader)

    assert reader.calls == []
