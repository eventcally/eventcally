"""Parity of the incoming/outgoing event reference pages. Written against the ORM
path first."""

from sqlalchemy import text


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def _set_created_at(app, db, reference_id, created_at):
    with app.app_context():
        db.session.execute(
            text("UPDATE eventreference SET created_at = :c WHERE id = :id"),
            {"c": created_at, "id": reference_id},
        )
        db.session.commit()


def test_incoming_pages(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    first_event_id = seeder.create_event(other_admin_unit_id, name="Erstes Event")
    second_event_id = seeder.create_event(other_admin_unit_id, name="Zweites Event")
    older_id = seeder.create_reference(first_event_id, admin_unit_id)
    newer_id = seeder.create_reference(second_event_id, admin_unit_id)
    _set_created_at(app, db, older_id, "2026-01-01")
    _set_created_at(app, db, newer_id, "2026-02-01")

    with app.app_context():
        db.session.execute(
            text("UPDATE eventreference SET rating = 70 WHERE id = :id"),
            {"id": older_id},
        )
        db.session.commit()

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.incoming_event_references", id=admin_unit_id)
    )
    rows = _rows(utils, response)
    assert rows == [
        "Zweites Event Anzeigen Bearbeiten Löschen Andere Crew 01.02.2026",
        "Erstes Event Anzeigen Bearbeiten Löschen Andere Crew 01.01.2026",
    ]

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.incoming_event_reference",
            id=admin_unit_id,
            event_reference_id=older_id,
        )
    )
    text_ = _text(utils, response)
    assert "Erstes Event" in text_
    assert "7/10" in text_

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.incoming_event_reference_update",
            id=admin_unit_id,
            event_reference_id=older_id,
        )
    )
    selected = (
        utils.get_soup(response)
        .find("select", attrs={"name": "rating"})
        .find("option", selected=True)
    )
    assert selected["value"] == "70"

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.incoming_event_reference_delete",
            id=admin_unit_id,
            event_reference_id=older_id,
        )
    )
    assert f"'Empfehlung {older_id}'" in _text(utils, response)

    second_admin_unit_id = seeder.create_admin_unit(user_id, "Zweite Crew")
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.incoming_event_reference",
            id=second_admin_unit_id,
            event_reference_id=older_id,
        )
    )


def test_outgoing_list(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id, name="Mein Event")
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    seeder.create_reference(event_id, other_admin_unit_id)

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.outgoing_event_references", id=admin_unit_id)
    )
    rows = _rows(utils, response)
    assert len(rows) == 1
    assert rows[0].startswith("Mein Event Veranstaltung anzeigen Andere Crew ")
