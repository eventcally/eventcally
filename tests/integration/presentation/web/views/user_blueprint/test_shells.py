"""The pages of the user area are shells of the `user` Vue entry; the BFF tests cover the
data and the writes."""

import datetime
import json

import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions

STATIC_ENDPOINTS = [
    "main.profile",
    "user.general",
    "user.notifications",
    "user.api_keys",
    "user.api_key_create",
    "user.oauth2_clients",
    "user.oauth2_client_create",
    "user.oauth2_tokens",
    "user.organization_members",
    "user.organization_member_invitations",
    "user.organization_invitations",
]


def _boot(utils, response):
    return json.loads(utils.get_soup(response).find("script", id="boot").string)


def _assert_shell(utils, response):
    boot = _boot(utils, response)
    assert boot["csrfToken"]
    assert boot["user"]["email"]


def _request_deletion(app, db, user_id):
    from project.infrastructure.models import User

    with app.app_context():
        user = db.session.get(User, user_id)
        user.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()


def _token_id(app, user_id):
    with app.app_context():
        from project.infrastructure.models import OAuth2Token

        return OAuth2Token.query.filter(OAuth2Token.user_id == user_id).first().id


# access


@pytest.mark.parametrize("endpoint", STATIC_ENDPOINTS)
def test_shell_pages(client, seeder: Seeder, utils: UtilActions, endpoint):
    seeder.setup_base()

    _assert_shell(utils, utils.get_endpoint_ok(endpoint))


@pytest.mark.parametrize(
    "endpoint, values",
    [(e, {}) for e in STATIC_ENDPOINTS if e != "main.profile"]
    + [
        ("main.profile", {}),
        ("user.request_deletion", {}),
        ("user.cancel_deletion", {}),
        ("user.accept_tos", {}),
        ("user.api_key", {"api_key_id": 1}),
        ("user.api_key_update", {"api_key_id": 1}),
        ("user.api_key_delete", {"api_key_id": 1}),
        ("user.oauth2_client", {"oauth2_client_id": 1}),
        ("user.oauth2_client_update", {"oauth2_client_id": 1}),
        ("user.oauth2_client_delete", {"oauth2_client_id": 1}),
        ("user.oauth2_token_revoke", {"oauth2_token_id": 1}),
        ("user.organization_member_delete", {"organization_member_id": 1}),
        (
            "user.organization_member_invitation_negotiate",
            {"organization_member_invitation_id": 1},
        ),
        (
            "user.organization_invitation_negotiate",
            {"organization_invitation_id": 1},
        ),
    ],
)
def test_anonymous_is_sent_to_the_login(client, utils, endpoint, values):
    url = utils.get_url(endpoint, **values)

    utils.assert_response_redirect_to_login(client.get(url), url)


def test_the_pages_are_get_only(client, seeder, utils):
    seeder.setup_base()
    shell = utils.get_ok(utils.get_url("user.general"))

    response = client.post(
        utils.get_url("user.general"),
        data={"csrf_token": _boot(utils, shell)["csrfToken"]},
    )

    assert response.status_code == 405


# request / cancel deletion


def test_request_deletion_page(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_base_event_verifier()

    _assert_shell(utils, utils.get_endpoint_ok("user.request_deletion"))


def test_request_deletion_of_an_administrator_is_refused(
    client, seeder: Seeder, utils: UtilActions
):
    seeder.setup_base()

    response = utils.get_endpoint("user.request_deletion")

    utils.assert_response_redirect(response, "main.manage_admin_units")
    utils.assert_response_error_message(
        utils.get_endpoint_ok("main.manage_admin_units"),
        "Du bist Administrator von mindestens einer Organisation. Beende deine Mitgliedschaft, um deinen Account zu löschen.",
    )


def test_request_deletion_twice_leads_to_the_cancel_page(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    _, _, member_id = seeder.setup_base_event_verifier()
    _request_deletion(app, db, member_id)

    utils.assert_response_redirect(
        utils.get_endpoint("user.request_deletion"), "user.cancel_deletion"
    )


def test_cancel_deletion_page(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, _ = seeder.setup_base()
    _request_deletion(app, db, user_id)

    _assert_shell(utils, utils.get_endpoint_ok("user.cancel_deletion"))


def test_cancel_deletion_without_a_request_leads_to_the_request_page(
    client, seeder: Seeder, utils: UtilActions
):
    seeder.setup_base()

    utils.assert_response_redirect(
        utils.get_endpoint("user.cancel_deletion"), "user.request_deletion"
    )


# accept ToS


def test_accept_tos_page(client, seeder: Seeder, utils: UtilActions):
    seeder.create_user(tos_accepted=False)
    utils.login()

    response = utils.get_endpoint("main.profile")
    utils.assert_response_redirect(
        response, "user.accept_tos", next="http://localhost/profile"
    )

    _assert_shell(utils, utils.get_endpoint_ok("user.accept_tos", next="/profile"))


def test_accept_tos_when_accepted_leads_to_next(
    client, seeder: Seeder, utils: UtilActions
):
    seeder.setup_base()

    response = utils.get_endpoint("user.accept_tos", next="/manage")

    utils.assert_response_redirect_to_url(response, "/manage")


# API keys and OAuth2 clients


def test_api_key_pages(client, seeder: Seeder, utils: UtilActions):
    user_id, _ = seeder.setup_base()
    api_key_id, _ = seeder.insert_default_api_key(user_id)

    for endpoint in ("user.api_key", "user.api_key_update", "user.api_key_delete"):
        response = utils.get_endpoint_ok(endpoint, api_key_id=api_key_id)
        _assert_shell(utils, response)


def test_foreign_and_organization_api_keys_are_unauthorized(
    client, seeder: Seeder, utils: UtilActions
):
    _, admin_unit_id = seeder.setup_base()
    other_id = seeder.create_user("other@test.de")
    foreign_id, _ = seeder.insert_default_api_key(other_id)
    organization_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    for endpoint in ("user.api_key", "user.api_key_update", "user.api_key_delete"):
        for api_key_id in (foreign_id, organization_key_id):
            utils.get_unauthorized(utils.get_url(endpoint, api_key_id=api_key_id))
        utils.assert_response_notFound(
            utils.get(utils.get_url(endpoint, api_key_id=4711))
        )


def test_oauth2_client_pages(client, seeder: Seeder, utils: UtilActions):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)

    for endpoint in (
        "user.oauth2_client",
        "user.oauth2_client_update",
        "user.oauth2_client_delete",
    ):
        response = utils.get_endpoint_ok(endpoint, oauth2_client_id=client_id)
        _assert_shell(utils, response)


def test_foreign_and_organization_oauth2_clients_are_unauthorized(
    client, seeder: Seeder, utils: UtilActions
):
    _, admin_unit_id = seeder.setup_base()
    other_id = seeder.create_user("other@test.de")
    foreign_id = seeder.insert_default_oauth2_client(other_id)
    organization_client_id = seeder.insert_default_oauth2_client(
        admin_unit_id=admin_unit_id
    )

    for endpoint in (
        "user.oauth2_client",
        "user.oauth2_client_update",
        "user.oauth2_client_delete",
    ):
        for client_id in (foreign_id, organization_client_id):
            utils.get_unauthorized(utils.get_url(endpoint, oauth2_client_id=client_id))
        utils.assert_response_notFound(
            utils.get(utils.get_url(endpoint, oauth2_client_id=4711))
        )


# OAuth2 tokens


def test_oauth2_token_revoke_page(client, app, seeder: Seeder, utils: UtilActions):
    user_id, _ = seeder.setup_api_access()
    utils.login()

    response = utils.get_endpoint_ok(
        "user.oauth2_token_revoke", oauth2_token_id=_token_id(app, user_id)
    )

    _assert_shell(utils, response)


def test_oauth2_token_that_is_revoked_leads_to_the_list(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    from project.infrastructure.models import OAuth2Token

    user_id, _ = seeder.setup_api_access()
    utils.login()
    token_id = _token_id(app, user_id)

    with app.app_context():
        db.session.get(OAuth2Token, token_id).access_token_revoked_at = 1
        db.session.commit()

    response = utils.get_endpoint("user.oauth2_token_revoke", oauth2_token_id=token_id)

    utils.assert_response_redirect(response, "user.oauth2_tokens")


def test_foreign_and_unknown_oauth2_tokens(client, app, seeder: Seeder, utils):
    other_user_id, _ = seeder.setup_api_access()
    token_id = _token_id(app, other_user_id)
    seeder.create_user("second@test.de")
    utils.login("second@test.de")

    utils.get_unauthorized(
        utils.get_url("user.oauth2_token_revoke", oauth2_token_id=token_id)
    )
    utils.assert_response_notFound(
        utils.get(utils.get_url("user.oauth2_token_revoke", oauth2_token_id=4711))
    )


# memberships


def _membership_id(app, user_id, admin_unit_id):
    from project.infrastructure.seed_helpers import get_member_for_admin_unit_by_user_id

    with app.app_context():
        return get_member_for_admin_unit_by_user_id(admin_unit_id, user_id).id


def test_leave_page(client, app, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["admin"], "second@test.de")

    response = utils.get_endpoint_ok(
        "user.organization_member_delete",
        organization_member_id=_membership_id(app, user_id, admin_unit_id),
    )

    _assert_shell(utils, response)


def test_the_last_administrator_cannot_leave(
    client, app, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint(
        "user.organization_member_delete",
        organization_member_id=_membership_id(app, user_id, admin_unit_id),
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_members", id=admin_unit_id
    )
    utils.assert_response_error_message(
        utils.get_endpoint_ok(
            "manage_admin_unit.organization_members", id=admin_unit_id
        ),
        "Der letzte verbleibende Administrator kann die Organisation nicht verlassen.",
    )


def test_foreign_and_unknown_memberships(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Fremde Crew")
    member_id = seeder.create_admin_unit_member(
        other_admin_unit_id, ["event_verifier"], "member@test.de"
    )

    utils.get_unauthorized(
        utils.get_url(
            "user.organization_member_delete", organization_member_id=member_id
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "user.organization_member_delete", organization_member_id=4711
            )
        )
    )


# invitations


def test_member_invitation_page(client, seeder: Seeder, utils: UtilActions):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    seeder.create_user("new@member.de")
    utils.login("new@member.de")
    invitation_id = seeder.create_invitation(admin_unit_id, "new@member.de")

    response = utils.get_endpoint_ok(
        "user.organization_member_invitation_negotiate",
        organization_member_invitation_id=invitation_id,
    )

    _assert_shell(utils, response)


def test_foreign_and_unknown_member_invitations(
    client, seeder: Seeder, utils: UtilActions
):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id, "Meine Crew")
    seeder.create_user("new@member.de")
    utils.login("new@member.de")
    invitation_id = seeder.create_invitation(admin_unit_id, "someone@else.de")

    utils.get_unauthorized(
        utils.get_url(
            "user.organization_member_invitation_negotiate",
            organization_member_invitation_id=invitation_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "user.organization_member_invitation_negotiate",
                organization_member_invitation_id=4711,
            )
        )
    )


def test_organization_invitation_page(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)
    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    response = utils.get_endpoint_ok(
        "user.organization_invitation_negotiate",
        organization_invitation_id=invitation_id,
    )

    _assert_shell(utils, response)


def test_foreign_and_unknown_organization_invitations(
    client, seeder: Seeder, utils: UtilActions
):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_user("new@member.de")
    utils.login("new@member.de")
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id, "someone@else.de"
    )

    utils.get_unauthorized(
        utils.get_url(
            "user.organization_invitation_negotiate",
            organization_invitation_id=invitation_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "user.organization_invitation_negotiate",
                organization_invitation_id=4711,
            )
        )
    )
