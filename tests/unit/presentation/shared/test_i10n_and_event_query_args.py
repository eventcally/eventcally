from types import SimpleNamespace

from project.presentation.shared import event_query_args, i10n


def test_get_locale_prefers_the_users_locale(monkeypatch):
    monkeypatch.setattr(
        i10n, "current_user", SimpleNamespace(is_authenticated=True, locale="de")
    )

    assert i10n.get_locale() == "de"


def test_reference_admin_unit_id_for_api(monkeypatch):
    from project.presentation.shared import current_admin_unit

    monkeypatch.setattr(
        event_query_args, "current_user", SimpleNamespace(is_authenticated=False)
    )
    assert event_query_args.reference_admin_unit_id_for_api() is None

    monkeypatch.setattr(
        event_query_args, "current_user", SimpleNamespace(is_authenticated=True)
    )
    monkeypatch.setattr(
        current_admin_unit, "get_current_admin_unit_for_api", lambda: None
    )
    assert event_query_args.reference_admin_unit_id_for_api() is None

    monkeypatch.setattr(
        current_admin_unit,
        "get_current_admin_unit_for_api",
        lambda: SimpleNamespace(id=4),
    )
    assert event_query_args.reference_admin_unit_id_for_api() == 4
