from types import SimpleNamespace

import pytest
from flask import Flask, g
from werkzeug.exceptions import HTTPException, NotFound, Unauthorized

from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.presentation.shared import access


class _Reader:
    def __init__(self, platform_admin=False, member=False):
        self.platform_admin, self.member = platform_admin, member

    def is_platform_admin(self, user_id):
        return self.platform_admin

    def member_has_permission(self, admin_unit_id, user_id, permission):
        return self.member


class _Authz:
    def __init__(self, reader=None, has_permission=False, planning=False):
        self.reader = reader or _Reader()
        self._has_permission = has_permission
        self._planning = planning

    def has_permission_for_admin_unit(self, actor, admin_unit_id, permission):
        return self._has_permission

    def can_use_planning(self, actor):
        return self._planning


class _QueryBus:
    def __init__(self, result=None):
        self.result = result
        self.queries = []

    def handle(self, query):
        self.queries.append(query)
        return self.result


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = False
    return app


@pytest.fixture
def ctx(app):
    with app.test_request_context():
        yield


def _patch(monkeypatch, actor=None, authz=None, bus=None, user=None, token=None):
    if actor is not None:
        monkeypatch.setattr(access, "_current_actor", lambda: actor)
    if authz is not None:
        monkeypatch.setattr(access, "_authorization", lambda: authz)
    if bus is not None:
        monkeypatch.setattr(access, "_query_bus", lambda: bus)
    monkeypatch.setattr(
        access,
        "current_user",
        user or SimpleNamespace(is_authenticated=True, id=1),
    )
    monkeypatch.setattr(access, "current_token", token)


def test_owner_access(ctx, monkeypatch):
    _patch(monkeypatch)

    assert access.has_owner_access(1) is True
    assert access.owner_access_or_401(1) is None
    with pytest.raises(Unauthorized):
        access.owner_access_or_401(2)


def test_login_api_user(ctx, monkeypatch):
    user = SimpleNamespace(id=9)

    _patch(monkeypatch, token=None)
    assert access.login_api_user() is False
    with pytest.raises(Unauthorized):
        access.login_api_user_or_401()

    _patch(monkeypatch, token=SimpleNamespace(user=user))
    assert access.login_api_user() is True
    assert g._login_user is user
    assert access.login_api_user_or_401() is None


def test_container_accessors(app):
    app.container = SimpleNamespace(
        cqrs=SimpleNamespace(
            query_bus=lambda: "bus", actor_authorization_service=lambda: "authz"
        )
    )

    with app.app_context():
        assert access._query_bus() == "bus"
        assert access._authorization() == "authz"


def test_current_actor(ctx, monkeypatch):
    from project.shared import context

    monkeypatch.setattr(
        context, "current_user", SimpleNamespace(is_authenticated=True, id=4)
    )
    monkeypatch.setattr(context, "current_token", None)

    assert access._current_actor().user_id == 4


def test_is_platform_admin(ctx, monkeypatch):
    _patch(monkeypatch, Actor(app_installation_id=1), _Authz())
    assert access.is_platform_admin() is False

    _patch(monkeypatch, Actor(user_id=1), _Authz(_Reader(platform_admin=True)))
    assert access.is_platform_admin() is True


def test_has_access_for_a_session_user_uses_the_policy(ctx, monkeypatch):
    unit = SimpleNamespace(id=2)

    _patch(monkeypatch, Actor(user_id=1), _Authz(has_permission=True))
    assert access.has_access(unit, "events:write") is True
    assert access.access_or_401(unit, "events:write") is None


def test_has_access_for_a_token_user_needs_membership(ctx, monkeypatch):
    unit = SimpleNamespace(id=2)
    token = SimpleNamespace(user=SimpleNamespace(id=1))
    authz = _Authz(_Reader(member=False), has_permission=True)

    _patch(monkeypatch, Actor(user_id=1), authz, token=token)
    assert access.has_access(unit, "events:write") is False
    with pytest.raises(Unauthorized):
        access.access_or_401(unit, "events:write")

    authz.reader.member = True
    assert access.has_access(unit, "events:write") is True


def test_admin_unit_owner_access(ctx):
    assert not access.has_admin_unit_owner_access(1)
    with pytest.raises(Unauthorized):
        access.admin_unit_owner_access_or_401(1)

    g.manage_admin_unit = SimpleNamespace(id=1)
    assert access.has_admin_unit_owner_access(1)
    assert access.admin_unit_owner_access_or_401(1) is None
    assert not access.has_admin_unit_owner_access(2)


def test_admin_units_with_user_permission(ctx, monkeypatch):
    units = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    _patch(monkeypatch, Actor(user_id=1), _Authz(), _QueryBus(units))
    monkeypatch.setattr(access, "has_access", lambda unit, perm: unit.id == 2)

    assert access.get_admin_units_with_current_user_permission("p") == [units[1]]


def test_admin_units_with_token_permission(ctx, monkeypatch):
    unit = SimpleNamespace(id=5)
    bus = _QueryBus(unit)
    installation = SimpleNamespace(admin_unit_id=5, permissions={"p"})

    _patch(monkeypatch, bus=bus, token=None)
    assert access.get_admin_units_with_current_token_permission("p") == []

    _patch(monkeypatch, bus=bus, token=SimpleNamespace(app_installation=None))
    assert access.get_admin_units_with_current_token_permission("p") == []

    _patch(monkeypatch, bus=bus, token=SimpleNamespace(app_installation=installation))
    assert access.get_admin_units_with_current_token_permission("other") == []
    assert access.get_admin_units_with_current_token_permission("p") == [unit]


def test_user_or_token_permission_dispatch(ctx, monkeypatch):
    monkeypatch.setattr(
        access, "get_admin_units_with_current_user_permission", lambda p: ["user"]
    )
    monkeypatch.setattr(
        access, "get_admin_units_with_current_token_permission", lambda p: ["token"]
    )

    _patch(monkeypatch, user=SimpleNamespace(is_authenticated=True))
    assert access.get_admin_units_with_current_user_or_token_permission("p") == ["user"]

    _patch(monkeypatch, user=SimpleNamespace(is_authenticated=False))
    assert access.get_admin_units_with_current_user_or_token_permission("p") == [
        "token"
    ]


def test_event_reference_helpers(ctx, monkeypatch):
    event = SimpleNamespace(admin_unit_id=1)
    units = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    monkeypatch.setattr(
        access,
        "get_admin_units_with_current_user_or_token_permission",
        lambda permission: units,
    )

    assert access.get_admin_units_for_event_reference(event) == [units[1]]
    assert access.can_reference_event(event) is True
    assert access.can_reference_event(SimpleNamespace(admin_unit_id=2)) is True

    monkeypatch.setattr(
        access, "get_admin_units_with_current_user_or_token_permission", lambda p: []
    )
    assert access.can_reference_event(event) is False


def test_can_request_event_reference(ctx, monkeypatch):
    bus = _QueryBus(True)
    _patch(monkeypatch, bus=bus)
    unit = SimpleNamespace(is_verified=True)
    event = SimpleNamespace(
        admin_unit=unit, admin_unit_id=1, public_status=EventPublicStatus.published
    )

    monkeypatch.setattr(access, "has_access", lambda u, p: False)
    assert access.can_request_event_reference_from_admin_unit(unit) is False
    assert access.can_request_event_reference(event) is False

    monkeypatch.setattr(access, "has_access", lambda u, p: True)
    assert access.can_request_event_reference_from_admin_unit(unit) is True
    assert (
        access.can_request_event_reference_from_admin_unit(
            SimpleNamespace(is_verified=False)
        )
        is False
    )
    assert access.can_request_event_reference(event) is True
    assert bus.queries[0].exclude_admin_unit_id == 1

    event.public_status = EventPublicStatus.draft
    assert access.can_request_event_reference(event) is False


def test_manage_queries(ctx, monkeypatch):
    bus = _QueryBus("result")
    _patch(monkeypatch, bus=bus)

    assert access.admin_units_the_current_user_is_member_of() == "result"
    assert bus.queries[-1].member_only is True
    assert access.get_admin_units_for_manage() == "result"
    assert access.get_admin_unit_for_manage(3) == "result"
    assert bus.queries[-1].id == 3


def test_get_admin_unit_for_manage_or_404(app, monkeypatch):
    app.login_manager = SimpleNamespace(unauthorized=lambda: 401)

    with app.test_request_context():
        _patch(monkeypatch, bus=_QueryBus("unit"))
        assert access.get_admin_unit_for_manage_or_404(1) == "unit"

        _patch(monkeypatch, bus=_QueryBus(None))
        with pytest.raises(NotFound):
            access.get_admin_unit_for_manage_or_404(1)

        _patch(
            monkeypatch,
            bus=_QueryBus(None),
            user=SimpleNamespace(is_authenticated=False),
        )
        with pytest.raises(HTTPException) as error:
            access.get_admin_unit_for_manage_or_404(1)
        assert error.value.code == 401


def test_can_create_admin_unit(app, monkeypatch):
    units = [SimpleNamespace(can_create_other=False)]
    _patch(monkeypatch, Actor(user_id=1), _Authz(), _QueryBus(units))

    with app.test_request_context():
        assert access.can_create_admin_unit() is True

        app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
        assert access.can_create_admin_unit() is False

        units[0].can_create_other = True
        assert access.can_create_admin_unit() is True

        units[0].can_create_other = False
        _patch(monkeypatch, Actor(user_id=1), _Authz(_Reader(True)), _QueryBus(units))
        assert access.can_create_admin_unit() is True


def test_can_use_planning(ctx, monkeypatch):
    _patch(monkeypatch, Actor(user_id=1), _Authz(planning=True))
    assert access.can_use_planning() is True


@pytest.mark.parametrize(
    "planning,units,can_create,invited,expected",
    [
        (True, [], False, False, True),
        (False, [1], False, False, True),
        (False, [], True, False, True),
        (False, [], False, True, True),
        (False, [], False, False, False),
    ],
)
def test_can_use_manage_place_lookup(
    ctx, monkeypatch, planning, units, can_create, invited, expected
):
    monkeypatch.setattr(access, "can_use_planning", lambda: planning)
    monkeypatch.setattr(access, "get_admin_units_for_manage", lambda: units)
    monkeypatch.setattr(access, "can_create_admin_unit", lambda: can_create)
    monkeypatch.setattr(access, "_has_organization_invitation", lambda: invited)

    assert access.can_use_manage_place_lookup() is expected


def test_has_organization_invitation(ctx, monkeypatch):
    _patch(monkeypatch, bus=_QueryBus(SimpleNamespace(items=[1])))
    assert access._has_organization_invitation() is True

    _patch(monkeypatch, bus=_QueryBus(SimpleNamespace(items=[])))
    assert access._has_organization_invitation() is False


def test_can_verify_admin_unit_user(ctx, monkeypatch):
    units = [SimpleNamespace(can_verify_other=False)]
    _patch(monkeypatch, Actor(user_id=1), _Authz(), _QueryBus(units))
    assert access.can_verify_admin_unit_user() is False

    units[0].can_verify_other = True
    assert access.can_verify_admin_unit_user() is True

    _patch(monkeypatch, user=SimpleNamespace(is_authenticated=False))
    assert access.can_verify_admin_unit_user() is False

    units[0].can_verify_other = False
    _patch(monkeypatch, Actor(user_id=1), _Authz(_Reader(True)), _QueryBus(units))
    assert access.can_verify_admin_unit_user() is True


def test_can_verify_admin_unit_token(ctx, monkeypatch):
    organization = SimpleNamespace(can_verify_other=True)
    installation = SimpleNamespace(admin_unit_id=5)

    _patch(monkeypatch, bus=_QueryBus(organization), token=None)
    assert access.can_verify_admin_unit_token() is False

    _patch(monkeypatch, token=SimpleNamespace(app_installation=None))
    assert access.can_verify_admin_unit_token() is False

    _patch(
        monkeypatch,
        bus=_QueryBus(organization),
        token=SimpleNamespace(app_installation=installation),
    )
    assert access.can_verify_admin_unit_token() is True


def test_can_verify_admin_unit_combines_user_and_token(ctx, monkeypatch):
    monkeypatch.setattr(access, "can_verify_admin_unit_user", lambda: False)
    monkeypatch.setattr(access, "can_verify_admin_unit_token", lambda: True)
    assert access.can_verify_admin_unit() is True


def test_can_current_user_delete_member(ctx, monkeypatch):
    member = SimpleNamespace(admin_unit_id=2, user_id=3)
    bus = _QueryBus(False)
    _patch(monkeypatch, Actor(user_id=1), _Authz(), bus)

    assert access.can_current_user_delete_member(member) is False
    assert (bus.queries[0].admin_unit_id, bus.queries[0].user_id) == (2, 3)

    _patch(monkeypatch, Actor(user_id=1), _Authz(_Reader(True)), bus)
    assert access.can_current_user_delete_member(member) is True
