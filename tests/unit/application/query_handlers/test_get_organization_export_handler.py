from datetime import datetime, timezone

import pytest

from project.application import queries
from project.application.query_handlers import GetOrganizationExportHandler
from project.application.read_models.organization_export_read_models import (
    OrganizationExportFile,
)
from project.application.services.abstract_organization_export_reader import (
    AbstractOrganizationExportReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader

FILE = OrganizationExportFile(
    size=10, created_at=datetime(2026, 10, 24, tzinfo=timezone.utc)
)


class FakeExportReader(AbstractOrganizationExportReader):
    def __init__(self, file=FILE):
        self.file = file
        self.calls = []

    def get_file(self, admin_unit_id):
        self.calls.append(admin_unit_id)
        return self.file

    def get_job_status(self, job_id):  # pragma: no cover
        raise NotImplementedError


def _handle(actor, reader):
    handler = GetOrganizationExportHandler(
        reader,
        ActorAuthorizationService(FakeReader(members=[(5, 7, "export:read")])),
    )
    return handler.handle(
        queries.GetOrganizationExportQuery(actor=actor, admin_unit_id=5)
    )


def test_member_reads_file():
    assert _handle(Actor(user_id=7), FakeExportReader()).file == FILE


def test_no_file():
    assert _handle(Actor(user_id=7), FakeExportReader(file=None)).file is None


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
def test_others_are_unauthorized_before_lookup(actor):
    reader = FakeExportReader()

    with pytest.raises(UnauthorizedError):
        _handle(actor, reader)

    assert reader.calls == []
