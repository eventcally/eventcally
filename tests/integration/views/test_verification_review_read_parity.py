"""Parity of the incoming verification request review page (organization profile
and members). Written against the ORM path first."""

import re

from sqlalchemy import text


def _card_texts(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(card.get_text().split()) for card in soup.select("div.card")]


def test_review_page_shows_profile_and_members(app, db, seeder, utils):
    (
        _,
        verifier_admin_unit_id,
        _,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    seeder.create_admin_unit_member(
        unverified_admin_unit_id, ["event_verifier"], "member@test.de"
    )
    image_id = seeder.upsert_default_image()

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE adminunit SET description = 'Beschreibung',"
                " url = 'https://example.com', email = 'crew@example.com',"
                " phone = '0123', fax = '0124', logo_id = :image_id WHERE id = :id"
            ),
            {"id": unverified_admin_unit_id, "image_id": image_id},
        )
        db.session.execute(
            text("UPDATE image SET copyright_text = 'EventCally' WHERE id = :id"),
            {"id": image_id},
        )
        db.session.commit()

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.incoming_organization_verification_request_review",
            id=verifier_admin_unit_id,
            organization_verification_request_id=request_id,
        )
    )
    cards = _card_texts(utils, response)
    soup = utils.get_soup(response)

    assert "Beschreibung" in cards[0]
    assert re.search(r"https://example\.com", cards[0])
    assert "crew@example.com" in cards[0]
    assert "0123" in cards[0] and "0124" in cards[0]
    assert "EventCally" in cards[0]
    assert soup.select_one("div.card img") is not None
    assert soup.select_one("div.card h5 i.fa-check-circle") is None
    assert "member@test.de Veranstaltungsexpert:in" in cards[1]
    assert cards[1].index("member@test.de") > 0
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.incoming_organization_verification_request_review",
                id=verifier_admin_unit_id,
                organization_verification_request_id=4711,
            )
        )
    )
