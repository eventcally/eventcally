def _event_url(event_id):
    return f"/bff/public/events/{event_id}"


def _date_url(event_date_id):
    return f"/bff/public/event-dates/{event_date_id}"


def _update_event(app, db, event_id, **values):
    from project.infrastructure.models import Event

    with app.app_context():
        event = db.session.get(Event, event_id)
        for key, value in values.items():
            setattr(event, key, value)
        db.session.commit()


def _private_event(app, db, seeder, log_in):
    user_id, admin_unit_id = seeder.setup_base(log_in=log_in)
    event_id = seeder.create_event(admin_unit_id, internal_tags="intern1,intern2")
    _update_event(app, db, event_id, rating=70, created_by_id=user_id)
    other_user_id, other_admin_unit_id = seeder.setup_base(
        email="other@test.de", name="Other Crew", log_in=False
    )
    seeder.create_reference_request(event_id, other_admin_unit_id)
    seeder.create_reference(event_id, other_admin_unit_id)
    return user_id, admin_unit_id, event_id


def test_get_event_anonymous(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, name="Stadtfest")

    body = utils.get_json_ok(_event_url(event_id)).json

    assert body["id"] == event_id
    assert body["name"] == "Stadtfest"
    assert body["organization_id"] == admin_unit_id
    assert body["organization"]["name"] == "Meine Crew"
    assert body["place"]["name"]
    assert body["organizer"]["name"] == "Meine Crew"
    assert body["public_status"] == "published"
    assert body["share_links"]["url"].endswith(f"/event/{event_id}")
    assert body["calendar_links"]["ics"].endswith(f"/event/{event_id}/ical")
    assert body["calendar_links"]["google"] is None
    assert len(body["dates"]) == 1
    assert body["categories"][0]["names"]


def test_get_event_hides_private_data_from_anonymous(client, app, db, seeder, utils):
    user_id, admin_unit_id, event_id = _private_event(app, db, seeder, log_in=False)

    body = utils.get_json_ok(_event_url(event_id)).json

    assert body["rating"] is None
    assert body["internal_tags"] is None
    assert body["reference_requests"] == []
    assert body["audit"]["created_at"]
    assert body["audit"]["created_by_label"] is None
    assert body["audit"]["updated_by_label"] is None
    assert not any(body["rights"].values())
    assert len(body["references"]) == 1


def test_get_event_shows_private_data_to_the_owner(client, app, db, seeder, utils):
    user_id, admin_unit_id, event_id = _private_event(app, db, seeder, log_in=True)

    body = utils.get_json_ok(_event_url(event_id)).json

    assert body["rating"] == 70
    assert body["internal_tags"] == "intern1,intern2"
    assert body["audit"]["created_by_label"] == "test@test.de"
    assert body["rights"]["can_update_event"]
    assert body["rights"]["can_create_reference_request"]
    assert len(body["reference_requests"]) == 1
    request = body["reference_requests"][0]
    assert request["review_status"] == "inbox"
    assert request["review_status_label"]
    assert request["organization"]["name"] == "Other Crew"


def test_get_event_hides_the_neutral_rating(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    _update_event(app, db, event_id, rating=50)

    assert utils.get_json_ok(_event_url(event_id)).json["rating"] is None


def test_get_event_rights_of_another_organization(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.setup_base(email="other@test.de", name="Other Crew", log_in=False)
    utils.login("other@test.de")

    rights = utils.get_json_ok(_event_url(event_id)).json["rights"]

    assert rights["can_reference_event"]
    assert rights["can_view_actions"]
    assert not rights["can_update_event"]
    assert not rights["can_create_reference_request"]


def test_get_event_unknown(client, app, db, seeder, utils):
    response = utils.get_json(_event_url(1234))
    utils.assert_response_notFound(response)


def test_get_event_draft_needs_access(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, draft=True)

    utils.assert_response_unauthorized(utils.get_json(_event_url(event_id)))

    utils.login()
    body = utils.get_json_ok(_event_url(event_id)).json
    assert body["public_status"] == "draft"


def test_get_event_of_unverified_organization(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False, admin_unit_verified=False)
    event_id = seeder.create_event(admin_unit_id)

    utils.assert_response_unauthorized(utils.get_json(_event_url(event_id)))


def test_get_event_date(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    event_date_id = seeder.get_event_date_id(event_id)

    body = utils.get_json_ok(_date_url(event_date_id)).json

    assert body["id"] == event_date_id
    assert body["start"]
    assert body["event"]["id"] == event_id
    assert body["event"]["share_links"]["url"].endswith(f"/eventdate/{event_date_id}")
    assert "google.com/calendar" in body["event"]["calendar_links"]["google"]
    assert body["event"]["calendar_links"]["ics"].endswith(
        f"/eventdate/{event_date_id}/ical"
    )


def test_get_event_date_never_sends_the_rating(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    _update_event(app, db, event_id, rating=70)
    event_date_id = seeder.get_event_date_id(event_id)

    body = utils.get_json_ok(_date_url(event_date_id)).json

    assert body["event"]["rating"] is None
    assert body["event"]["rights"]["can_update_event"]


def test_get_event_date_unknown(client, app, db, seeder, utils):
    utils.assert_response_notFound(utils.get_json(_date_url(1234)))
