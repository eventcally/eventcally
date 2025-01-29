import pytest


def create_form_data(response, utils):
    return {
        "csrf_token": utils.get_csrf(response),
        "name": "Meine Crew",
        "short_name": "meine_crew",
        "location-csrf_token": utils.get_csrf(response, "location"),
        "location-postalCode": "38640",
        "location-city": "Goslar",
        "logo-csrf_token": utils.get_csrf(response, "logo"),
        "submit": "Submit",
    }


def test_create(client, app, utils, seeder):
    seeder.create_user()
    utils.login()
    response = client.get("/admin_unit/create")
    assert response.status_code == 200

    data = create_form_data(response, utils)
    data["logo-image_base64"] = seeder.get_default_image_upload_base64()
    data["logo-copyright_text"] = "EventCally"

    with client:
        response = client.post(
            "/admin_unit/create",
            data=data,
        )
        assert response.status_code == 302

        with app.app_context():
            from project.access import has_current_user_member_role_for_admin_unit
            from project.services.admin_unit import get_admin_unit_by_name
            from project.services.organizer import get_event_organizer
            from project.services.place import get_event_place

            admin_unit = get_admin_unit_by_name("Meine Crew")
            assert admin_unit is not None
            assert admin_unit.name == "Meine Crew"
            assert admin_unit.location.city == "Goslar"
            assert admin_unit.location.postalCode == "38640"
            assert has_current_user_member_role_for_admin_unit(admin_unit.id, "admin")
            assert has_current_user_member_role_for_admin_unit(
                admin_unit.id, "event_verifier"
            )

            organizer = get_event_organizer(admin_unit.id, "Meine Crew")
            assert organizer.name == "Meine Crew"
            assert organizer.location.city == "Goslar"
            assert organizer.location.postalCode == "38640"

            place = get_event_place(admin_unit.id, "Goslar")
            assert place.name == "Goslar"
            assert place.location.city == "Goslar"
            assert place.location.postalCode == "38640"


def test_create_duplicate(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")

    response = client.get("/admin_unit/create")
    assert response.status_code == 200

    with client:
        response = client.post(
            "/admin_unit/create",
            data=create_form_data(response, utils),
        )
        assert response.status_code == 200
        assert b"duplicate" in response.data


def test_create_requiresAdmin_nonAdmin(client, app, utils, seeder):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True

    seeder.create_user()
    utils.login()

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)
    utils.assert_response_redirect(response, "manage_admin_units")


def test_create_requiresAdmin_globalAdmin(client, app, utils, seeder):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.create_user(admin=True)
    utils.login()

    url = utils.get_url("admin_unit_create")
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Meine Crew",
            "short_name": "meine_crew",
            "location-postalCode": "38640",
            "location-city": "Goslar",
        },
    )
    assert response.status_code == 302


def test_create_requiresAdmin_memberOfOrgWithoutFlag(client, app, utils, seeder):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.setup_base()

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)
    utils.assert_response_redirect(response, "manage_admin_units")


def test_create_requiresAdmin_memberOfOrgWithFlag(client, app, utils, seeder):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    user_id = seeder.create_user(admin=False)
    utils.login()
    seeder.create_admin_unit(user_id, can_create_other=True)

    url = utils.get_url("admin_unit_create")
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Other Crew",
            "short_name": "other_crew",
            "location-postalCode": "38640",
            "location-city": "Goslar",
        },
    )
    assert response.status_code == 302


def test_create_from_invitation(client, app, db, utils, seeder, mocker):
    mail_mock = utils.mock_send_mails_async(mocker)
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(
        user_id, can_invite_other=True, can_verify_other=True
    )
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id,
        relation_auto_verify_event_reference_requests=True,
        relation_verify=True,
    )

    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")
    url = utils.get_url("admin_unit_create", invitation_id=invitation_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "short_name": "invitedorganization",
            "location-postalCode": "38640",
            "location-city": "Goslar",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        from project.models import AdminUnitInvitation
        from project.services.admin_unit import get_admin_unit_by_name

        admin_unit = get_admin_unit_by_name("Invited Organization")
        assert admin_unit is not None

        relation = admin_unit.incoming_relations[0]
        assert relation.source_admin_unit_id == admin_unit_id
        assert relation.auto_verify_event_reference_requests
        assert relation.verify
        assert relation.invited
        relation_id = relation.id

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation is None

    relation_url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_update",
        id=admin_unit_id,
        organization_relation_id=relation_id,
    )
    utils.assert_send_mail_called(mail_mock, "test@test.de", relation_url)


def test_create_from_invitation_currentUserDoesNotMatchInvitationEmail(
    client, app, utils, seeder
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(
        user_id, can_invite_other=True, can_verify_other=True
    )
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id,
        relation_auto_verify_event_reference_requests=True,
        relation_verify=True,
    )

    seeder.create_user("other@test.de")
    utils.login("other@test.de")
    url = utils.get_url("admin_unit_create", invitation_id=invitation_id)
    response = utils.get(url)
    utils.assert_response_redirect(response, "manage_admin_units")


def test_create_with_relation(client, app, utils, seeder):
    user_id = seeder.create_user(admin=False)
    utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, can_verify_other=True)

    url = utils.get_url("admin_unit_create")
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Other Crew",
            "short_name": "other_crew",
            "location-postalCode": "38640",
            "location-city": "Goslar",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        from project.services.admin_unit import get_admin_unit_by_name

        admin_unit = get_admin_unit_by_name("Other Crew")
        assert admin_unit is not None

        relation = admin_unit.incoming_relations[0]
        assert relation.source_admin_unit_id == admin_unit_id
        assert relation.auto_verify_event_reference_requests is False
        assert relation.verify


def test_update(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Initial name")

    url = "/admin_unit/%d/update" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data=create_form_data(response, utils),
        )
        assert response.status_code == 302

        with app.app_context():
            from project.services.admin_unit import get_admin_unit_by_id

            admin_unit_from_db = get_admin_unit_by_id(admin_unit_id)
            assert admin_unit_from_db is not None
            assert admin_unit_from_db.name == "Meine Crew"


def test_update_duplicate(client, app, utils, seeder):
    user_id = seeder.create_user()
    utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")
    admin_unit_id = seeder.create_admin_unit(user_id, "Other Crew")

    url = "/admin_unit/%d/update" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data=create_form_data(response, utils),
        )
        assert response.status_code == 200
        assert b"duplicate" in response.data


def test_update_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    url = "/admin_unit/%d/update" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 302


def test_list(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")
    response = client.get("/manage/admin_units")
    assert b"Meine Crew" in response.data


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_admin_unit_request_deletion(
    client, seeder, utils, app, db, mocker, db_error, non_match
):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("admin_unit_request_deletion", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Meine Crew"

    if non_match:
        form_name = "wrong"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Der eingegebene Name entspricht nicht dem Namen der Organisation"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "manage_admin_unit", id=admin_unit_id)

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert admin_unit.deletion_requested_at is not None


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_admin_unit_cancel_deletion(
    client, seeder, utils, app, db, mocker, db_error, non_match
):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        import datetime

        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()

    url = utils.get_url("admin_unit_cancel_deletion", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Meine Crew"

    if non_match:
        form_name = "wrong"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Der eingegebene Name entspricht nicht dem Namen der Organisation"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "manage_admin_unit", id=admin_unit_id)

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert admin_unit.deletion_requested_at is None


def test_admin_unit_cancel_deletion_permission_missing(client, seeder, utils, mocker):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()

    response = utils.get_endpoint("admin_unit_cancel_deletion", id=admin_unit_id)
    utils.assert_response_permission_missing(
        response, "manage_admin_unit", id=admin_unit_id
    )
