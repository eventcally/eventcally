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
    utils.register()
    response = client.get("/admin_unit/create")
    assert response.status_code == 200

    data = create_form_data(response, utils)
    data["logo-image_file"] = seeder.get_default_image_upload()

    with client:
        response = client.post(
            "/admin_unit/create",
            data=data,
        )
        assert response.status_code == 302

        with app.app_context():
            from project.services.admin_unit import get_admin_unit_by_name
            from project.services.organizer import get_event_organizer
            from project.access import has_current_user_role_for_admin_unit

            admin_unit = get_admin_unit_by_name("Meine Crew")
            assert admin_unit is not None
            assert admin_unit.name == "Meine Crew"
            assert admin_unit.location.city == "Goslar"
            assert admin_unit.location.postalCode == "38640"
            assert has_current_user_role_for_admin_unit(admin_unit, "admin")
            assert has_current_user_role_for_admin_unit(admin_unit, "event_verifier")

            organizer = get_event_organizer(admin_unit.id, "Meine Crew")
            assert organizer.name == "Meine Crew"
            assert organizer.location.city == "Goslar"
            assert organizer.location.postalCode == "38640"
            assert organizer is not None


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
