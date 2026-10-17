"""SqlAlchemyOrganizationInvitationReadRepository against the database, on the read
session."""

from datetime import datetime

import pytest
from sqlalchemy import text

from project.application.queries import (
    ListOrganizationInvitationsQuery,
    OrganizationInvitationSort,
    PageRequest,
    TrackableCriteria,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.organization_invitation_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def _set_trackable(app, db, invitation_id, created_at, updated_at=None):
    with app.app_context():
        db.session.execute(
            text(
                "UPDATE adminunitinvitation"
                " SET created_at = :created_at, updated_at = :updated_at"
                " WHERE id = :id"
            ),
            {"id": invitation_id, "created_at": created_at, "updated_at": updated_at},
        )
        db.session.commit()


@pytest.fixture
def invitations(app, db, seeder):
    """Organization "Meine Crew" with four invitations and fixed timestamps, plus one
    invitation of another organization."""
    _, admin_unit_id = seeder.setup_base(log_in=False)
    _, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Andere Crew", log_in=False
    )
    ids = {
        "full": seeder.create_admin_unit_invitation(
            admin_unit_id,
            email="full@test.de",
            admin_unit_name="Voll",
            relation_auto_verify_event_reference_requests=True,
            relation_verify=True,
        ),
        "alpha": seeder.create_admin_unit_invitation(admin_unit_id, "alpha@test.de"),
        "bare": seeder.create_admin_unit_invitation(
            admin_unit_id, "bare@test.de", admin_unit_name=None
        ),
        "bravo": seeder.create_admin_unit_invitation(admin_unit_id, "bravo@test.de"),
        "other": seeder.create_admin_unit_invitation(
            other_admin_unit_id, "other-invited@test.de"
        ),
    }
    _set_trackable(
        app, db, ids["full"], datetime(2026, 1, 1, 10), datetime(2026, 3, 1, 12)
    )
    _set_trackable(app, db, ids["alpha"], datetime(2026, 2, 1, 9))
    _set_trackable(
        app, db, ids["bare"], datetime(2026, 1, 15, 14), datetime(2026, 2, 20, 16)
    )
    _set_trackable(app, db, ids["bravo"], datetime(2026, 3, 5, 18))
    _set_trackable(app, db, ids["other"], datetime(2026, 1, 5))

    return {"admin_unit_id": admin_unit_id, "ids": ids}


def _list(read_repo, invitations, **kwargs):
    query = ListOrganizationInvitationsQuery(
        admin_unit_id=invitations["admin_unit_id"], **kwargs
    )
    return read_repo("list", query)


def _emails(page):
    return [item.email for item in page.items]


def test_organization_exists(read_repo, invitations):
    assert read_repo("organization_exists", invitations["admin_unit_id"])
    assert not read_repo("organization_exists", 4711)


def test_list_is_scoped_to_the_organization_in_id_order(read_repo, invitations):
    page = _list(read_repo, invitations)

    assert _emails(page) == [
        "full@test.de",
        "alpha@test.de",
        "bare@test.de",
        "bravo@test.de",
    ]
    assert page.total == 4


@pytest.mark.parametrize(
    "sort, expected",
    [
        (
            OrganizationInvitationSort.created_at_desc,
            ["bravo", "alpha", "bare", "full"],
        ),
        (
            OrganizationInvitationSort.updated_at_desc,
            ["full", "bare", "alpha", "bravo"],
        ),
        (
            OrganizationInvitationSort.last_modified_at_desc,
            ["bravo", "full", "bare", "alpha"],
        ),
    ],
)
def test_list_sort(read_repo, invitations, sort, expected):
    page = _list(read_repo, invitations, sort=sort)

    assert _emails(page) == [f"{name}@test.de" for name in expected]


@pytest.mark.parametrize(
    "criteria, expected",
    [
        ({"created_at_from": datetime(2026, 1, 12)}, ["alpha", "bare", "bravo"]),
        # Regression: the legacy path also bounded last_modified_at by created_at_to.
        ({"created_at_to": datetime(2026, 2, 2)}, ["full", "alpha", "bare"]),
        (
            {
                "updated_at_from": datetime(2026, 2, 1),
                "updated_at_to": datetime(2026, 2, 28),
            },
            ["bare"],
        ),
        (
            {
                "last_modified_at_from": datetime(2026, 2, 1),
                "last_modified_at_to": datetime(2026, 3, 2),
            },
            ["full", "alpha", "bare"],
        ),
    ],
)
def test_list_trackable_bounds(read_repo, invitations, criteria, expected):
    page = _list(read_repo, invitations, trackable=TrackableCriteria(**criteria))

    assert _emails(page) == [f"{name}@test.de" for name in expected]


def test_list_paging(read_repo, invitations):
    second = _list(read_repo, invitations, page=PageRequest(page=2, per_page=3))
    out_of_range = _list(read_repo, invitations, page=PageRequest(page=4, per_page=2))

    assert _emails(second) == ["bravo@test.de"]
    assert second.total == 4
    assert out_of_range.items == []


def test_list_item_fields(read_repo, invitations):
    page = _list(read_repo, invitations)
    full, _, bare, _ = page.items

    assert full.id == invitations["ids"]["full"]
    assert full.admin_unit_name == "Voll"
    assert full.created_at == datetime(2026, 1, 1, 10)
    assert full.updated_at == datetime(2026, 3, 1, 12)
    assert full.last_modified_at == datetime(2026, 3, 1, 12)
    assert bare.admin_unit_name is None
    assert bare.last_modified_at == datetime(2026, 2, 20, 16)


def test_get_detail_with_organization_ref(read_repo, invitations):
    detail = read_repo("get", invitations["ids"]["full"])

    assert detail.id == invitations["ids"]["full"]
    assert detail.email == "full@test.de"
    assert detail.admin_unit_id == invitations["admin_unit_id"]
    assert detail.admin_unit_name == "Voll"
    assert detail.relation_auto_verify_event_reference_requests is True
    assert detail.relation_verify is True
    assert detail.created_at == datetime(2026, 1, 1, 10)
    assert detail.admin_unit.id == invitations["admin_unit_id"]
    assert detail.admin_unit.name == "Meine Crew"


def test_get_unknown_returns_none(read_repo, invitations):
    assert read_repo("get", 4711) is None


def test_list_for_user_matches_email_ignoring_case(read_repo, seeder, invitations):
    from project.application.queries import ListUserOrganizationInvitationsQuery

    ids = invitations["ids"]
    seeder.create_admin_unit_invitation(
        invitations["admin_unit_id"], "ALPHA@test.de", admin_unit_name="Zweite"
    )
    alpha_user_id = seeder.create_user("Alpha@Test.de")

    page = read_repo(
        "list_for_user", ListUserOrganizationInvitationsQuery(user_id=alpha_user_id)
    )

    assert page.items[0].id == ids["alpha"]
    assert [item.admin_unit_name for item in page.items][1] == "Zweite"
    assert page.total == 2
    assert page.items[0].admin_unit.name == "Meine Crew"


def test_get_recipient_email(read_repo, invitations):
    assert read_repo("get_recipient_email", invitations["ids"]["full"]) == (
        "full@test.de"
    )
    assert read_repo("get_recipient_email", 4711) is None
