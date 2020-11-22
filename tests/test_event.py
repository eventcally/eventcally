def test_read(client, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    event_id = seeder.create_event(admin_unit_id)

    url = "/event/%d" % event_id
    response = client.get(url)
    assert response.status_code == 200


def test_create(client, app, utils, seeder, mocker):
    user_id = seeder.create_user()
    utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = "/admin_unit/%d/events/create" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        from project.scrape.form import Form
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.data, "html.parser")
        form = Form(soup.find("form"))
        data = form.fill(
            {
                "name": "Name",
                "description": "Beschreibung",
                "start": ["2030-12-31", "23", "59"],
                "event_place_choice": "2",
                "new_event_place-name": "Platz",
                "organizer_id": "1",
            }
        )

        response = client.post(
            url,
            data=data,
        )
        assert response.status_code == 302
        assert (
            response.headers["Location"]
            == "http://localhost/manage/admin_unit/%d/events" % admin_unit_id
        )

        with app.app_context():
            from project.models import Event

            event = (
                Event.query.filter(Event.admin_unit_id == admin_unit_id)
                .filter(Event.name == "Name")
                .first()
            )
            assert event is not None
