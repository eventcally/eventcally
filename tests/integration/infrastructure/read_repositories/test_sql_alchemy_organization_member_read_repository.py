"""SqlAlchemyOrganizationMemberReadRepository against the database, on the read
session."""

import pytest

from project.application.queries import (
    ListOrganizationMembersQuery,
    ListUserOrganizationMembershipsQuery,
    PageRequest,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.organization_member_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


@pytest.fixture
def members(seeder):
    owner_id, admin_unit_id = seeder.setup_base(log_in=False)
    zeta_id = seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier"], "Zeta@test.de"
    )
    alpha_id = seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier", "admin"], "alpha@test.de"
    )
    other_owner_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_owner_id, "Andere Crew")
    return owner_id, admin_unit_id, other_admin_unit_id, alpha_id, zeta_id


def test_organization_exists(read_repo, members):
    _, admin_unit_id, _, _, _ = members

    assert read_repo("organization_exists", admin_unit_id) is True
    assert read_repo("organization_exists", 4711) is False


def test_list_is_scoped_and_ordered_by_email(read_repo, members):
    _, admin_unit_id, _, alpha_id, _ = members

    page = read_repo("list", ListOrganizationMembersQuery(admin_unit_id=admin_unit_id))

    assert [item.user.email for item in page.items] == [
        "alpha@test.de",
        "test@test.de",
        "Zeta@test.de",
    ]
    assert page.total == 3
    alpha = page.items[0]
    assert alpha.id == alpha_id
    assert alpha.admin_unit_id == admin_unit_id
    assert [role.name for role in alpha.roles] == ["admin", "event_verifier"]
    assert [role.title for role in alpha.roles] == ["Administrator", "Event expert"]


def test_list_pages(read_repo, members):
    _, admin_unit_id, _, _, _ = members

    page = read_repo(
        "list",
        ListOrganizationMembersQuery(
            admin_unit_id=admin_unit_id, page=PageRequest(page=2, per_page=2)
        ),
    )

    assert [item.user.email for item in page.items] == ["Zeta@test.de"]
    assert page.total == 3


def test_get(read_repo, members):
    _, admin_unit_id, _, _, zeta_id = members

    member = read_repo("get", zeta_id)

    assert member.user.email == "Zeta@test.de"
    assert str(member.user) == "Zeta@test.de"
    assert member.admin_unit_id == admin_unit_id
    assert [role.name for role in member.roles] == ["event_verifier"]
    assert read_repo("get", 4711) is None


def test_memberships_of_user(read_repo, seeder, members):
    owner_id, admin_unit_id, _, _, _ = members
    second_admin_unit_id = seeder.create_admin_unit(owner_id, "Zweite Crew")

    page = read_repo(
        "list_for_user", ListUserOrganizationMembershipsQuery(user_id=owner_id)
    )

    assert [item.admin_unit.name for item in page.items] == [
        "Meine Crew",
        "Zweite Crew",
    ]
    assert [item.admin_unit_id for item in page.items] == [
        admin_unit_id,
        second_admin_unit_id,
    ]
    assert all(item.user_id == owner_id for item in page.items)

    membership = read_repo("get_membership", page.items[1].id)
    assert membership == page.items[1]
    assert read_repo("get_membership", 4711) is None


def test_roles(read_repo, members):
    roles = read_repo("list_roles")

    assert [role.name for role in roles] == ["admin", "event_verifier"]
