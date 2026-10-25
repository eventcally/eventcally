from types import SimpleNamespace

import pytest
from flask import Flask

from project.domain.errors import UnauthorizedError
from project.presentation.shared import organization_create as module


class _QueryBus:
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def handle(self, query):
        if self.error:
            raise self.error
        return self.result


def _app(query_bus):
    app = Flask(__name__)
    app.container = SimpleNamespace(cqrs=SimpleNamespace(query_bus=lambda: query_bus))
    return app


def test_invitation_found():
    invitation = SimpleNamespace(id=1)

    with _app(_QueryBus(invitation)).app_context():
        gate = module.check_organization_create(1)

    assert gate.invitation is invitation
    assert gate.denial is None


def test_invitation_missing():
    with _app(_QueryBus(None)).app_context():
        assert module.check_organization_create(1).denial == "invitation_missing"


def test_invitation_forbidden():
    with _app(_QueryBus(error=UnauthorizedError())).app_context():
        assert module.check_organization_create(1).denial == "invitation_forbidden"


def test_closed_when_the_user_cannot_create(monkeypatch):
    monkeypatch.setattr(module, "can_create_admin_unit", lambda: False)

    assert module.check_organization_create(None).denial == "closed"
    assert module.check_organization_create(0).denial == "closed"


def test_denied_when_deletion_was_requested(monkeypatch):
    monkeypatch.setattr(module, "can_create_admin_unit", lambda: True)
    monkeypatch.setattr(
        module, "current_user", SimpleNamespace(deletion_requested_at="2030-01-01")
    )

    assert module.check_organization_create(None).denial == "deletion_requested"


def test_open_gate(monkeypatch):
    monkeypatch.setattr(module, "can_create_admin_unit", lambda: True)
    monkeypatch.setattr(
        module, "current_user", SimpleNamespace(deletion_requested_at=None)
    )

    gate = module.check_organization_create(None)

    assert gate.denial is None
    assert gate.invitation is None


def _unit(can_verify_other=False, incoming_reference_requests_allowed=False):
    return SimpleNamespace(
        can_verify_other=can_verify_other,
        incoming_reference_requests_allowed=incoming_reference_requests_allowed,
    )


def test_embedded_relation_options_none_for_invitations():
    assert module.get_embedded_relation_options(SimpleNamespace()) is None


@pytest.mark.parametrize(
    "unit,access",
    [(None, True), (_unit(True), False), (_unit(False, False), True)],
)
def test_embedded_relation_options_none_without_unit_access_or_options(
    monkeypatch, unit, access
):
    monkeypatch.setattr(module, "get_current_admin_unit", lambda: unit)
    monkeypatch.setattr(module, "has_access", lambda admin_unit, permission: access)

    assert module.get_embedded_relation_options(None) is None


def test_embedded_relation_options(monkeypatch):
    unit = _unit(can_verify_other=True, incoming_reference_requests_allowed=None)
    monkeypatch.setattr(module, "get_current_admin_unit", lambda: unit)
    monkeypatch.setattr(module, "has_access", lambda admin_unit, permission: True)

    options = module.get_embedded_relation_options(None)

    assert options.admin_unit is unit
    assert options.can_verify is True
    assert options.can_auto_verify is False
