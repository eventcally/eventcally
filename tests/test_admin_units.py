def test_admin_unit_create(client, app, utils):
    utils.register()
    response = client.get("/admin_unit/create")
    assert response.status_code == 200

    response = client.post(
        "/admin_unit/create",
        data={
            "csrf_token": utils.get_csrf(response),
            "name": "Meine Crew",
            "short_name": "meine_crew",
            "location-csrf_token": utils.get_csrf(response, "location"),
            "location-postalCode": "38640",
            "location-city": "Goslar",
            "logo-csrf_token": utils.get_csrf(response, "logo"),
            "submit": "Submit",
        },
    )
    assert response.status_code == 302

    with app.app_context():
        from project.services.admin_unit import get_admin_unit

        admin_unit = get_admin_unit("Meine Crew")
        assert admin_unit is not None
