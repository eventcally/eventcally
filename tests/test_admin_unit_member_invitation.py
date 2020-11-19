def test_create(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = "/manage/admin_unit/%d/members/invite" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        mail_mock = utils.mock_send_mails(mocker)
        email = "new@member.de"
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "roles": "admin",
                "submit": "Submit",
            },
        )
        assert response.status_code == 302
        utils.assert_send_mail_called(mail_mock, email)

        with app.app_context():
            from project.services.admin_unit import find_admin_unit_member_invitation

            invitation = find_admin_unit_member_invitation(email, admin_unit_id)
            assert invitation.roles == "admin"


def test_create_db_error(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = "/manage/admin_unit/%d/members/invite" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)
        email = "new@member.de"
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "roles": "admin",
                "submit": "Submit",
            },
        )
        assert response.status_code == 200
        assert b"MockException" in response.data


def test_create_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    url = "/manage/admin_unit/%d/members/invite" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 302


def test_read_new_member_not_registered(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    with app.app_context():
        from project.services.admin_unit import insert_admin_unit_member_invitation

        invitation = insert_admin_unit_member_invitation(
            admin_unit_id, email, ["admin"]
        )
        invitation_id = invitation.id

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost/register"


def test_delete(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    with app.app_context():
        from project.services.admin_unit import insert_admin_unit_member_invitation

        invitation = insert_admin_unit_member_invitation(
            admin_unit_id, email, ["admin"]
        )
        invitation_id = invitation.id

    url = "/manage/invitation/%d/delete" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "submit": "Submit",
            },
        )
        assert response.status_code == 302

        with app.app_context():
            from project.services.admin_unit import find_admin_unit_member_invitation

            invitation = find_admin_unit_member_invitation(email, admin_unit_id)
            assert invitation is None


def test_delete_db_error(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    with app.app_context():
        from project.services.admin_unit import insert_admin_unit_member_invitation

        invitation = insert_admin_unit_member_invitation(
            admin_unit_id, email, ["admin"]
        )
        invitation_id = invitation.id

    url = "/manage/invitation/%d/delete" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)

        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "submit": "Submit",
            },
        )

        assert response.status_code == 200
        assert b"MockException" in response.data


def test_delete_email_does_not_match(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    with app.app_context():
        from project.services.admin_unit import insert_admin_unit_member_invitation

        invitation = insert_admin_unit_member_invitation(
            admin_unit_id, email, ["admin"]
        )
        invitation_id = invitation.id

    url = "/manage/invitation/%d/delete" % invitation_id
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


def test_delete_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    email = "new@member.de"
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    with app.app_context():
        from project.services.admin_unit import insert_admin_unit_member_invitation

        invitation = insert_admin_unit_member_invitation(
            admin_unit_id, email, ["admin"]
        )
        invitation_id = invitation.id

    url = "/manage/invitation/%d/delete" % invitation_id

    response = client.get(url)
    assert response.status_code == 302
