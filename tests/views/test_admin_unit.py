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
