from types import SimpleNamespace

from project.shared import context
from project.shared.context import ContextProvider


def test_current_user_id_or_none_authenticated(monkeypatch):
    monkeypatch.setattr(
        context, "current_user", SimpleNamespace(is_authenticated=True, id=7)
    )
    assert ContextProvider().current_user_id_or_none == 7


def test_current_user_id_or_none_anonymous(monkeypatch):
    monkeypatch.setattr(
        context, "current_user", SimpleNamespace(is_authenticated=False)
    )
    assert ContextProvider().current_user_id_or_none is None


def test_current_app_installation_id_or_none(monkeypatch):
    provider = ContextProvider()

    monkeypatch.setattr(
        context, "current_token", SimpleNamespace(app_installation_id=3)
    )
    assert provider.current_app_installation_id_or_none == 3

    monkeypatch.setattr(context, "current_token", None)
    assert provider.current_app_installation_id_or_none is None


def test_current_actor(monkeypatch):
    monkeypatch.setattr(
        context, "current_user", SimpleNamespace(is_authenticated=True, id=7)
    )
    monkeypatch.setattr(
        context, "current_token", SimpleNamespace(app_installation_id=3)
    )

    actor = ContextProvider().current_actor

    assert actor.user_id == 7
    assert actor.app_installation_id == 3
