import pytest

from project.application import commands
from project.application.command_handlers.start_organization_export_handler import (
    StartOrganizationExportHandler,
)
from project.application.services.abstract_organization_export_dispatcher import (
    AbstractOrganizationExportDispatcher,
)
from project.application.services.organization_export_jobs import (
    is_organization_export_job_id,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.conftest import ACTOR, grant_permission


class FakeDispatcher(AbstractOrganizationExportDispatcher):
    def __init__(self, tracked=True):
        self.tracked = tracked
        self.calls = []

    def start(self, admin_unit_id, job_id):
        self.calls.append((admin_unit_id, job_id))
        return self.tracked


def _cmd():
    return commands.StartOrganizationExportCommand.model_construct(
        actor=ACTOR, admin_unit_id=5
    )


def test_member_starts_export(uow):
    grant_permission(uow, 5, "export:read")
    dispatcher = FakeDispatcher()

    result = StartOrganizationExportHandler(dispatcher).handle(_cmd(), uow)

    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0][0] == 5
    assert result.job_id == dispatcher.calls[0][1]
    assert is_organization_export_job_id(5, result.job_id)


def test_eager_export_has_no_job_to_track(uow):
    grant_permission(uow, 5, "export:read")
    dispatcher = FakeDispatcher(tracked=False)

    result = StartOrganizationExportHandler(dispatcher).handle(_cmd(), uow)

    assert len(dispatcher.calls) == 1
    assert result.job_id is None


def test_without_permission_nothing_is_dispatched(uow):
    dispatcher = FakeDispatcher()

    with pytest.raises(UnauthorizedError):
        StartOrganizationExportHandler(dispatcher).handle(_cmd(), uow)

    assert dispatcher.calls == []
