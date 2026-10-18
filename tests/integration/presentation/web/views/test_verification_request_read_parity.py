"""Parity of the organization verification request lists and outgoing pages.
Written against the ORM path first."""

from sqlalchemy import text


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def _set(app, db, request_id, sql):
    with app.app_context():
        db.session.execute(
            text(f"UPDATE adminunitverificationrequest SET {sql} WHERE id = :id"),
            {"id": request_id},
        )
        db.session.commit()


def test_incoming_list_and_filter(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    alpha_user_id = seeder.create_user("alpha@test.de")
    alpha_id = seeder.create_admin_unit(alpha_user_id, "Alpha Crew", verified=False)
    beta_user_id = seeder.create_user("beta@test.de")
    beta_id = seeder.create_admin_unit(beta_user_id, "Beta Crew", verified=False)
    old_id = seeder.create_admin_unit_verification_request(alpha_id, admin_unit_id)
    new_id = seeder.create_admin_unit_verification_request(beta_id, admin_unit_id)
    _set(app, db, old_id, "created_at = '2026-01-01', review_status = 3")
    _set(app, db, new_id, "created_at = '2026-02-01'")

    url = "manage_admin_unit.incoming_organization_verification_requests"
    response = utils.get_ok(utils.get_url(url, id=admin_unit_id))
    rows = _rows(utils, response)
    assert rows[0].startswith("Beta Crew")
    assert "Ungeprüft" in rows[0] and "01.02.2026" in rows[0]
    assert rows[1].startswith("Alpha Crew")
    assert "Abgelehnt" in rows[1]

    response = utils.get_ok(utils.get_url(url, id=admin_unit_id, review_status=3))
    rows = _rows(utils, response)
    assert len(rows) == 1 and rows[0].startswith("Alpha Crew")


def test_outgoing_pages(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    verifier_user_id = seeder.create_user("verifier@test.de")
    verifier_id = seeder.create_admin_unit(verifier_user_id, "Verifier Crew")
    request_id = seeder.create_admin_unit_verification_request(
        admin_unit_id, verifier_id
    )
    _set(app, db, request_id, "review_status = 3, rejection_reason = 3")

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_verification_requests",
            id=admin_unit_id,
        )
    )
    rows = _rows(utils, response)
    assert len(rows) == 1 and rows[0].startswith("Verifier Crew")

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_verification_request",
            id=admin_unit_id,
            organization_verification_request_id=request_id,
        )
    )
    text_ = _text(utils, response)
    assert "Verifier Crew" in text_
    assert "Abgelehnt" in text_
    assert "Unbekannt" in text_

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_verification_request_delete",
            id=admin_unit_id,
            organization_verification_request_id=request_id,
        )
    )
    assert f"'Verifizierungsanfrage {request_id}'" in _text(utils, response)

    second_admin_unit_id = seeder.create_admin_unit(
        user_id, "Zweite Crew", verified=True
    )
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_verification_request",
            id=second_admin_unit_id,
            organization_verification_request_id=request_id,
        )
    )
