import pytest

from project.application import queries
from project.application.query_handlers import GetSettingsForAdminHandler
from project.application.read_models.settings_read_model import SettingsReadModel
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.unit.application.services.test_event_visibility_service import FakeReader


class FakeRepo(AbstractSiteSettingsReadRepository):
    def get_site_notices(self):
        raise NotImplementedError

    def get_settings(self):
        return SettingsReadModel(tos="T")


def _handle(actor):
    handler = GetSettingsForAdminHandler(
        FakeRepo(), ActorAuthorizationService(FakeReader(admins=[7]))
    )
    return handler.handle(queries.GetSettingsForAdminQuery(actor=actor))


def test_platform_admin_reads_settings():
    assert _handle(Actor(user_id=7)).tos == "T"


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
def test_others_are_unauthorized(actor):
    with pytest.raises(UnauthorizedError):
        _handle(actor)
