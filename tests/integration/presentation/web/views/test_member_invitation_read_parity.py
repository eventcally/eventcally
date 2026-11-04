"""Parity of the member invitation pages (manage and invited user). Written against
the ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def test_manage_list_orders_by_email(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_invitation(admin_unit_id, "Zeta@test.de")
    seeder.create_invitation(admin_unit_id, "alpha@test.de")

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.organization_member_invitations", id=admin_unit_id
        )
    )

    assert [row.split(" ")[0] for row in _rows(utils, response)] == [
        "alpha@test.de",
        "Zeta@test.de",
    ]


def test_manage_update_and_delete_pages(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_invitation(
        admin_unit_id, "invited@test.de", ["event_verifier"]
    )

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.organization_member_invitation_update",
            id=admin_unit_id,
            organization_member_invitation_id=invitation_id,
        )
    )
    soup = utils.get_soup(response)
    checked = [
        box["value"]
        for box in soup.find_all("input", attrs={"name": "roles"})
        if box.has_attr("checked")
    ]
    assert checked == ["event_verifier"]
    assert "invited@test.de" in _text(utils, response)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.organization_member_invitation_delete",
            id=admin_unit_id,
            organization_member_invitation_id=invitation_id,
        )
    )
    assert f"Möchtest du 'Mitgliedschaftseinladung {invitation_id}' löschen?" in _text(
        utils, response
    )


def test_manage_invitation_of_other_organization(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de")
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.organization_member_invitation_update",
            id=other_admin_unit_id,
            organization_member_invitation_id=invitation_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.organization_member_invitation_delete",
                id=admin_unit_id,
                organization_member_invitation_id=4711,
            )
        )
    )


def test_invitation_link_of_unknown_invitation(seeder, utils):
    seeder.setup_base()

    utils.assert_response_notFound(
        utils.get(utils.get_url("main.admin_unit_member_invitation", id=4711))
    )
