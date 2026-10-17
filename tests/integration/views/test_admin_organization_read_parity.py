"""Parity of the admin area organization pages. Written against the ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _first_cells(utils, response):
    soup = utils.get_soup(response)
    return [
        next(row.find("td").stripped_strings) for row in soup.select("table tbody tr")
    ]


def test_list_search_and_pages(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin=True, name="Meine Crew")
    seeder.create_admin_unit(
        seeder.create_user("a@test.de"), "alpha Crew", verified=False
    )
    seeder.create_admin_unit(
        seeder.create_user("z@test.de"), "Zeta Crew", verified=True
    )

    response = utils.get_ok(utils.get_url("admin.organizations"))
    names = _first_cells(utils, response)
    assert (
        names.index("alpha Crew") < names.index("Meine Crew") < names.index("Zeta Crew")
    )
    verified_cells = {
        next(row.find("td").stripped_strings): str(row.find_all("td")[1])
        for row in utils.get_soup(response).select("table tbody tr")
    }
    assert verified_cells["alpha Crew"] != verified_cells["Zeta Crew"]
    assert verified_cells["Zeta Crew"] == verified_cells["Meine Crew"]

    response = utils.get_ok(utils.get_url("admin.organizations", keyword="zet"))
    assert _first_cells(utils, response) == ["Zeta Crew"]

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

    response = utils.get_ok(
        utils.get_url("admin.organization_update", id=admin_unit_id)
    )
    soup = utils.get_soup(response)
    assert soup.find("input", attrs={"name": "can_verify_other"}).has_attr("checked")
    assert soup.find("input", attrs={"name": "can_invite_other"}).has_attr("checked")
    assert not soup.find("input", attrs={"name": "can_create_other"}).has_attr(
        "checked"
    )
    assert "Meine Crew" in _text(utils, response)

    response = utils.get_ok(
        utils.get_url("admin.organization_delete", id=admin_unit_id)
    )
    assert "Möchtest du 'Meine Crew' löschen?" in _text(utils, response)

    utils.assert_response_notFound(
        utils.get(utils.get_url("admin.organization_update", id=4711))
    )
