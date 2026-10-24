def _review_url(utils, admin_unit_id, reference_request_id):
    return utils.get_url(
        "manage_admin_unit.incoming_event_reference_request_review",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )


def test_review_renders_the_shell(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        admin_unit_id
    )

    response = utils.get_ok(_review_url(utils, admin_unit_id, reference_request_id))

    assert b'<div id="app"' in response.data
    assert "Empfehlungsanfrage prüfen".encode() in response.data


def test_review_of_a_verified_request_redirects_to_the_list(
    client, seeder, utils, app, db
):
    _, admin_unit_id = seeder.setup_base()
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        reference_request.review_status = EventReferenceRequestReviewStatus.verified
        db.session.commit()

    response = client.get(_review_url(utils, admin_unit_id, reference_request_id))

    utils.assert_response_redirect(
        response,
        "manage_admin_unit.incoming_event_reference_requests",
        id=admin_unit_id,
    )
    with client.session_transaction() as session:
        categories = [category for category, _ in session["_flashes"]]
    assert categories == ["danger"]


def test_review_unauthorized_redirects_to_login(client, seeder, utils):
    seeder.create_user()
    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        third_admin_unit_id
    )
    url = _review_url(utils, third_admin_unit_id, reference_request_id)

    response = client.get(url)

    utils.assert_response_redirect_to_login(response, url)


def test_review_status(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_outgoing_reference_request(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.outgoing_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.get_ok(url)


def test_review_status_404_third(client, seeder, utils):
    seeder.create_user()
    seeder._utils.login()

    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(third_admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.outgoing_event_reference_request",
        id=third_admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    response = client.get(url)
    assert response.status_code == 404


def test_review_status_unauthorized_redirects_to_login(client, seeder, utils):
    seeder.create_user()

    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(third_admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.outgoing_event_reference_request",
        id=third_admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    response = client.get(url)
    utils.assert_response_redirect_to_login(response, url)
