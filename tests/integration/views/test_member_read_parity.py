"""Parity of the organization member pages (manage list/update/delete and the user's
membership list/leave page). Written against the ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def test_manage_list_orders_by_email_and_shows_roles(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["event_verifier"], "Zeta@test.de")
    seeder.create_admin_unit_member(
        admin_unit_id, ["admin", "event_verifier"], "alpha@test.de"
    )

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.organization_members", id=admin_unit_id)
    )
    rows = _rows(utils, response)

    assert [row.split(" ")[0] for row in rows] == [
        "alpha@test.de",
        "test@test.de",
        "Zeta@test.de",
    ]
    assert "Administrator:in, Veranstaltungsexpert:in" in rows[0]
    assert "Veranstaltungsexpert:in" in rows[2]


def test_manage_update_prefills_roles_and_email(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    member_id = seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier"], "member@test.de"
    )

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.organization_member_update",
            id=admin_unit_id,
            organization_member_id=member_id,
        )
    )
    soup = utils.get_soup(response)

    checked = [
        box["value"]
        for box in soup.find_all("input", attrs={"name": "role_names"})
        if box.has_attr("checked")
    ]
    choices = [
        box["value"] for box in soup.find_all("input", attrs={"name": "role_names"})
    ]
    assert checked == ["event_verifier"]
    assert choices == ["admin", "event_verifier"]
    assert "member@test.de" in _text(utils, response)


def test_manage_delete_shows_member_email(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    member_id = seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier"], "member@test.de"
    )

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.organization_member_delete",
            id=admin_unit_id,
            organization_member_id=member_id,
        )
    )

    assert "Möchtest du 'member@test.de' löschen?" in _text(utils, response)


def test_manage_member_of_other_organization(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    member_id = seeder.create_admin_unit_member(
        admin_unit_id, ["event_verifier"], "member@test.de"
    )
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.organization_member_update",
            id=other_admin_unit_id,
            organization_member_id=member_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.organization_member_update",
                id=admin_unit_id,
                organization_member_id=4711,
            )
        )
    )


def test_user_membership_list_and_leave_page(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit(user_id, "Andere Crew")
    other_owner_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_owner_id, "Fremde Crew")

    response = utils.get_ok(utils.get_url("user.organization_members"))
    text = _text(utils, response)

    assert "Meine Crew" in text
    assert "Andere Crew" in text
    assert "Fremde Crew" not in text


def test_user_leave_page_of_other_user_is_unauthorized(seeder, utils):
    seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Fremde Crew")
    member_id = seeder.create_admin_unit_member(
        other_admin_unit_id, ["event_verifier"], "member@test.de"
    )

    utils.get_unauthorized(
        utils.get_url(
            "user.organization_member_delete", organization_member_id=member_id
        )
    )


def test_user_leave_page_shows_organization(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_admin_unit_member(admin_unit_id, ["admin"], "admin.member@test.de")
    response = utils.get_ok(utils.get_url("user.organization_members"))
    leave_url = next(
        link["href"]
        for link in utils.get_soup(response).find_all("a")
        if "/delete" in link.get("href", "")
    )

    response = utils.get_ok(leave_url)

    assert "Meine Crew" in _text(utils, response)
