"""Custom widget query handlers — fake repository."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetCustomWidgetHandler,
    ListCustomWidgetsHandler,
)
from project.application.read_models.custom_widget_read_models import (
    CustomWidgetReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_custom_widget_read_repository import (
    AbstractCustomWidgetReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.unit.application.query_handlers.authz_helpers import ACTOR, authz

WIDGET = CustomWidgetReadModel(
    id=1,
    admin_unit_id=7,
    widget_type="search",
    name="Widget",
    admin_unit=OrganizationRefReadModel(id=7, name="Crew"),
)


class FakeRepo(AbstractCustomWidgetReadRepository):
    def organization_exists(self, admin_unit_id):
        return admin_unit_id == 7

    def list(self, query):
        return Page(items=[WIDGET], page=1, per_page=20, total=1)

    def get(self, object_id):
        return WIDGET if object_id == 1 else None


def test_list_requires_permission():
    query = queries.ListCustomWidgetsQuery(admin_unit_id=7, name="wid", actor=ACTOR)

    assert (
        ListCustomWidgetsHandler(FakeRepo(), authz("custom_widgets:read"))
        .handle(query)
        .total
        == 1
    )
    assert (
        ListCustomWidgetsHandler(FakeRepo(), authz("custom_widgets:read")).handle(
            queries.ListCustomWidgetsQuery(admin_unit_id=8, actor=ACTOR)
        )
        is None
    )
    with pytest.raises(UnauthorizedError):
        ListCustomWidgetsHandler(FakeRepo(), authz()).handle(query)


def test_get_is_public():
    assert (
        GetCustomWidgetHandler(FakeRepo()).handle(queries.GetCustomWidgetQuery(id=1))
        == WIDGET
    )
    assert (
        GetCustomWidgetHandler(FakeRepo()).handle(queries.GetCustomWidgetQuery(id=2))
        is None
    )
