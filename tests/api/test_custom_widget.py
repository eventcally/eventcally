def test_read(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("api_v1_custom_widget", id=custom_widget_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["settings"]["color"] == "black"


def test_put(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("api_v1_custom_widget", id=custom_widget_id)
    response = utils.put_json(url, {"widget_type": "search", "name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import CustomWidget

        custom_widget = db.session.get(CustomWidget, custom_widget_id)
        assert custom_widget.name == "Neuer Name"
        assert custom_widget.widget_type == "search"


def test_patch(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("api_v1_custom_widget", id=custom_widget_id)
    response = utils.patch_json(url, {"name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import CustomWidget

        custom_widget = db.session.get(CustomWidget, custom_widget_id)
        assert custom_widget.name == "Neuer Name"
        assert custom_widget.widget_type == "search"


def test_delete(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_api_access()
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("api_v1_custom_widget", id=custom_widget_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import CustomWidget

        custom_widget = db.session.get(CustomWidget, custom_widget_id)
        assert custom_widget is None
