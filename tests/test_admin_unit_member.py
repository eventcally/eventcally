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


def test_delete(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)

    url = "/manage/member/%d/delete" % member_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": "test@test.de",
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
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)

    url = "/manage/member/%d/delete" % member_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)

        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": "test@test.de",
                "submit": "Submit",
            },
        )

        assert response.status_code == 200
        assert b"MockException" in response.data


def test_delete_email_does_not_match(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)

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


def test_delete_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    url = "/manage/member/%d/delete" % member_id
    response = client.get(url)
    assert response.status_code == 302
