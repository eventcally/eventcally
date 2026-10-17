"""Byte-level parity of the user API read endpoints (snapshot captured on the ORM
path, see `tests/api/read_parity.py`)."""

from datetime import datetime

from tests.api.read_parity import assert_matches_snapshot, set_trackable


def test_user_invitations_and_memberships_match_snapshot(app, db, seeder, utils):
    owner_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    second_admin_unit_id = seeder.create_admin_unit(owner_id, "Zweite Crew")
    invited_user_id = seeder.create_user("invited@test.de")
    ids = [
        seeder.create_admin_unit_invitation(
            admin_unit_id, email="Invited@test.de", admin_unit_name="Alpha"
        ),
        seeder.create_admin_unit_invitation(
            second_admin_unit_id, email="invited@test.de", admin_unit_name="Bravo"
        ),
        seeder.create_admin_unit_invitation(
            admin_unit_id, email="invited@TEST.de", admin_unit_name=None
        ),
    ]
    foreign_id = seeder.create_admin_unit_invitation(admin_unit_id, email="x@test.de")
    seeder.create_admin_unit_member(admin_unit_id, ["event_verifier"], "m@test.de")

    with app.app_context():
        for object_id, (created_at, updated_at) in zip(
            ids,
            [
                (datetime(2026, 1, 1, 10), datetime(2026, 3, 1, 12)),
                (datetime(2026, 2, 1, 9), None),
                (datetime(2026, 1, 15, 14), datetime(2026, 2, 20, 16)),
            ],
        ):
            set_trackable(db, "adminunitinvitation", object_id, created_at, updated_at)
        db.session.commit()

    from project.cli.seed_helpers import (
        add_user_to_admin_unit_with_roles,
        get_admin_unit_by_id,
    )
    from project.user_datastore import get_user

    with app.app_context():
        add_user_to_admin_unit_with_roles(
            get_user(invited_user_id), get_admin_unit_by_id(admin_unit_id), ["admin"]
        )
        add_user_to_admin_unit_with_roles(
            get_user(invited_user_id),
            get_admin_unit_by_id(second_admin_unit_id),
            ["event_verifier"],
        )
        db.session.commit()

    utils.login("invited@test.de")

    def inv_list(**kwargs):
        return utils.get_url("api_v1_user_organization_invitation_list", **kwargs)

    requests = {
        "invitations": inv_list(),
        "invitations_sort_name": inv_list(sort="name"),
        "invitations_sort_updated_at": inv_list(sort="-updated_at"),
        "invitations_sort_last_modified_at": inv_list(sort="-last_modified_at"),
        "invitations_created_at_from": inv_list(created_at_from="2026-01-12T00:00:00"),
        "invitations_updated_at_range": inv_list(
            updated_at_from="2026-02-01T00:00:00", updated_at_to="2026-02-28T00:00:00"
        ),
        "invitations_page_2": inv_list(page=2, per_page=2),
        "invitations_out_of_range": inv_list(page=4, per_page=2),
        "invitation": utils.get_url("api_v1_user_organization_invitation", id=ids[1]),
        "invitation_foreign": utils.get_url(
            "api_v1_user_organization_invitation", id=foreign_id
        ),
        "invitation_unknown": utils.get_url(
            "api_v1_user_organization_invitation", id=4711
        ),
        "memberships": utils.get_url("api_v1_user_organization_membership_list"),
        "memberships_page_2": utils.get_url(
            "api_v1_user_organization_membership_list", page=2, per_page=1
        ),
    }

    assert_matches_snapshot("user", utils, requests)


def test_user_app_installations_match_snapshot(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    other_owner_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_owner_id, "Andere Crew")
    foreign_admin_unit_id = seeder.create_admin_unit(other_owner_id, "Fremde Crew")
    seeder.create_admin_unit_member(other_admin_unit_id, ["event_verifier"], "x@t.de")

    from project.cli.seed_helpers import (
        add_user_to_admin_unit_with_roles,
        get_admin_unit_by_id,
    )
    from project.user_datastore import get_user

    with app.app_context():
        add_user_to_admin_unit_with_roles(
            get_user(user_id),
            get_admin_unit_by_id(other_admin_unit_id),
            ["event_verifier"],
        )
        db.session.commit()

    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    seeder.install_app(app_id, admin_unit_id)
    seeder.install_app(app_id, other_admin_unit_id)
    seeder.install_app(app_id, foreign_admin_unit_id)
    seeder.authorize_api_access_with_client(app_id, user_id, admin_unit_id)

    requests = {
        "installations": utils.get_url("api_v1_user_app_installation_list"),
        "installations_admin_only": utils.get_url(
            "api_v1_user_app_installation_list", admin_only=1
        ),
        "installations_page_2": utils.get_url(
            "api_v1_user_app_installation_list", page=2, per_page=1
        ),
    }

    assert_matches_snapshot("user_app_installations", utils, requests)
