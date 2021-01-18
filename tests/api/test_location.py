def test_read(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        from project.models import Location

        location = Location()
        location.street = "Markt 7"
        location.postalCode = "38640"
        location.city = "Goslar"
        location.latitude = 51.9077888
        location.longitude = 10.4333312

        db.session.add(location)
        db.session.commit()
        location_id = location.id

    url = utils.get_url("api_v1_location", id=location_id)
    response = utils.get_ok(url)
    assert response.json["latitude"] == "51.9077888000000000"
