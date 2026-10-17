"""Parity of the incoming/outgoing event reference request lists and the outgoing
read page. Written against the ORM path first."""

from sqlalchemy import text


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def _requests(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    incoming_old = seeder.create_reference_request(
        seeder.create_event(other_admin_unit_id, name="Altes Event"), admin_unit_id
    )
    incoming_new = seeder.create_reference_request(
        seeder.create_event(other_admin_unit_id, name="Neues Event"), admin_unit_id
    )
    outgoing = seeder.create_reference_request(
        seeder.create_event(admin_unit_id, name="Mein Event"), other_admin_unit_id
    )

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE eventreferencerequest SET created_at = '2026-01-01',"
                " review_status = 3, rejection_reason = 1 WHERE id = :id"
            ),
            {"id": incoming_old},
        )
        db.session.execute(
            text(
                "UPDATE eventreferencerequest SET created_at = '2026-02-01'"
                " WHERE id = :id"
            ),
            {"id": incoming_new},
        )
        db.session.execute(
            text(
                "UPDATE eventreferencerequest SET review_status = 3,"
                " rejection_reason = 2 WHERE id = :id"
            ),
            {"id": outgoing},
        )
        db.session.commit()

    return (
        user_id,
        admin_unit_id,
        other_admin_unit_id,
        incoming_old,
        incoming_new,
        outgoing,
    )


def test_incoming_list_filter_and_actions(app, db, seeder, utils):
    _, admin_unit_id, _, incoming_old, incoming_new, _ = _requests(app, db, seeder)
    url = "manage_admin_unit.incoming_event_reference_requests"

    response = utils.get_ok(utils.get_url(url, id=admin_unit_id))
    rows = _rows(utils, response)
    assert rows[0].startswith("Neues Event")
    assert "Anfrage prüfen" in rows[0]
    assert "Andere Crew 01.02.2026" in rows[0]
    assert rows[1].startswith("Altes Event")
    assert "Abgelehnt" in rows[1]

    response = utils.get_ok(utils.get_url(url, id=admin_unit_id, review_status=3))
    rows = _rows(utils, response)
    assert len(rows) == 1 and rows[0].startswith("Altes Event")


def test_outgoing_list_and_read(app, db, seeder, utils):
    user_id, admin_unit_id, _, _, _, outgoing = _requests(app, db, seeder)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_requests", id=admin_unit_id
        )
    )
    rows = _rows(utils, response)
    assert len(rows) == 1
    assert rows[0].startswith("Mein Event")
    assert "Andere Crew" in rows[0]

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_request",
            id=admin_unit_id,
            event_reference_request_id=outgoing,
        )
    )
    text_ = _text(utils, response)
    assert "Mein Event" in text_
    assert "Abgelehnt" in text_
    assert "Andere Crew" in text_

    second_admin_unit_id = seeder.create_admin_unit(user_id, "Zweite Crew")
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_request",
            id=second_admin_unit_id,
            event_reference_request_id=outgoing,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.outgoing_event_reference_request",
                id=admin_unit_id,
                event_reference_request_id=4711,
            )
        )
    )
