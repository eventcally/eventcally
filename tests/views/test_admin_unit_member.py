import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_update(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)

    url = "/manage/member/%d/update" % member_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "roles": "admin",
                "submit": "Submit",
            },
        )
        assert response.status_code == 302

        with app.app_context():
            from project.services.admin_unit import get_admin_unit_member

            member = get_admin_unit_member(member_id)
            assert len(member.roles) == 1
            assert any(r.name == "admin" for r in member.roles)


def test_update_db_error(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)

    url = "/manage/member/%d/update" % member_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)

        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "roles": "admin",
                "submit": "Submit",
            },
        )
        assert response.status_code == 200
        assert b"MockException" in response.data


def test_update_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    url = "/manage/member/%d/update" % member_id
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.parametrize("scenario", ["default", "current_user"])
def test_delete(client, app, db, utils: UtilActions, seeder: Seeder, scenario: str):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_email = "test@test.de" if scenario == "current_user" else "member@test.de"
    member_id = seeder.create_admin_unit_member_event_verifier(
        admin_unit_id, email=member_email
    )

    url = "/manage/member/%d/delete" % member_id
    response = client.get(url)

    if scenario == "current_user":
        utils.assert_response_redirect(
            response, "manage_admin_unit_delete_membership", id=admin_unit_id
        )
        return

    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": "member@test.de",
                "submit": "Submit",
            },
        )
        assert response.status_code == 302

        with app.app_context():
            from project.services.admin_unit import get_admin_unit_member

            member = get_admin_unit_member(member_id)
            assert member is None


def test_delete_db_error(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(
        admin_unit_id, email="member@test.de"
    )

    url = "/manage/member/%d/delete" % member_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)

        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": "member@test.de",
                "submit": "Submit",
            },
        )

        assert response.status_code == 200
        assert b"MockException" in response.data


def test_delete_email_does_not_match(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(
        admin_unit_id, email="member@test.de"
    )

    url = "/manage/member/%d/delete" % member_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": "wrong@test.de",
                "submit": "Submit",
            },
        )
        assert response.status_code == 200
        assert b"Die eingegebene Email passt nicht zur Email" in response.data
