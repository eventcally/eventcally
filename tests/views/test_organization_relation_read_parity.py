"""Parity of the outgoing organization relation pages. Written against the ORM path
first."""

from sqlalchemy import text


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _first_cells(utils, response):
    soup = utils.get_soup(response)
    return [
        next(row.find("td").stripped_strings) for row in soup.select("table tbody tr")
    ]


def _relations(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    alpha_id = seeder.create_admin_unit(seeder.create_user("a@test.de"), "alpha Crew")
    beta_id = seeder.create_admin_unit(seeder.create_user("b@test.de"), "Beta Crew")
    gamma_id = seeder.create_admin_unit(seeder.create_user("c@test.de"), "Gamma Crew")
    alpha_rel = seeder.create_admin_unit_relation(admin_unit_id, alpha_id, verify=True)
    beta_rel = seeder.create_admin_unit_relation(
        admin_unit_id, beta_id, auto_verify_event_reference_requests=True
    )
    seeder.create_admin_unit_relation(admin_unit_id, gamma_id)

    with app.app_context():
        for unit_id, updated in [
            (alpha_id, "2026-01-01"),
            (beta_id, "2026-03-01"),
            (gamma_id, "2026-02-01"),
        ]:
            db.session.execute(
                text("UPDATE adminunit SET updated_at = :u WHERE id = :id"),
                {"u": updated, "id": unit_id},
            )
        db.session.commit()

    return user_id, admin_unit_id, alpha_rel, beta_rel


def test_list_sort_search_filters(app, db, seeder, utils):
    _, admin_unit_id, _, _ = _relations(app, db, seeder)
    url = "manage_admin_unit.outgoing_organization_relations"

    response = utils.get_ok(utils.get_url(url, id=admin_unit_id))
    assert _first_cells(utils, response) == ["alpha Crew", "Beta Crew", "Gamma Crew"]

    response = utils.get_ok(
        utils.get_url(url, id=admin_unit_id, sort="-last_modified_at")
    )
    assert _first_cells(utils, response) == ["Beta Crew", "Gamma Crew", "alpha Crew"]

    response = utils.get_ok(utils.get_url(url, id=admin_unit_id, keyword="be"))
    assert _first_cells(utils, response) == ["Beta Crew"]

    response = utils.get_ok(
        utils.get_url(url, id=admin_unit_id, auto_verify_event_reference_requests="0")
    )
    assert _first_cells(utils, response) == ["alpha Crew", "Gamma Crew"]


def test_update_and_delete_pages(app, db, seeder, utils):
    user_id, admin_unit_id, alpha_rel, beta_rel = _relations(app, db, seeder)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_relation_update",
            id=admin_unit_id,
            organization_relation_id=beta_rel,
        )
    )
    soup = utils.get_soup(response)
    assert soup.find(
        "input", attrs={"name": "auto_verify_event_reference_requests"}
    ).has_attr("checked")
    assert "Beta Crew" in _text(utils, response)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_relation_delete",
            id=admin_unit_id,
            organization_relation_id=alpha_rel,
        )
    )
    assert f"'Beziehung {alpha_rel}'" in _text(utils, response)

    second_admin_unit_id = seeder.create_admin_unit(user_id, "Zweite Crew")
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_relation_update",
            id=second_admin_unit_id,
            organization_relation_id=alpha_rel,
        )
    )
