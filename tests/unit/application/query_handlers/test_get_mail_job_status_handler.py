import pytest

from project.application import queries
from project.application.query_handlers import GetMailJobStatusHandler
from project.application.read_models.mail_job_read_models import MailJobStatusReadModel
from project.application.services.abstract_mail_job_status_reader import (
    AbstractMailJobStatusReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader


class FakeStatusReader(AbstractMailJobStatusReader):
    def __init__(self):
        self.calls = []

    def get(self, job_id):
        self.calls.append(job_id)
        if job_id != "known":
            return None
        return MailJobStatusReadModel(job_id=job_id, count=2, completed=1, ready=False)


def _handle(actor, job_id, reader):
    handler = GetMailJobStatusHandler(
        reader, ActorAuthorizationService(FakeReader(admins=[7]))
    )
    return handler.handle(queries.GetMailJobStatusQuery(actor=actor, job_id=job_id))


def test_platform_admin_reads_status():
    status = _handle(Actor(user_id=7), "known", FakeStatusReader())

    assert status.completed == 1


def test_unknown_job_is_none():
    assert _handle(Actor(user_id=7), "other", FakeStatusReader()) is None


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
def test_others_are_unauthorized_before_lookup(actor):
    reader = FakeStatusReader()

    with pytest.raises(UnauthorizedError):
        _handle(actor, "known", reader)

    assert reader.calls == []
