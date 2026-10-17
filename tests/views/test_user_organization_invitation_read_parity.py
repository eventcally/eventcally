"""Parity of the invited user's organization invitation pages. Written against the
ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def test_user_list_and_negotiate(seeder, utils):
    owner_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_admin_unit_id = seeder.create_admin_unit(owner_id, "Andere Crew")
    seeder.create_user("New@Member.de")
    utils.login("New@Member.de")
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id, "new@member.de", admin_unit_name="Neue Crew"
    )
    seeder.create_admin_unit_invitation(other_admin_unit_id, "someone@else.de")

    response = utils.get_ok(utils.get_url("user.organization_invitations"))
    text = _text(utils, response)
    assert "Meine Crew" in text
    assert "Neue Crew" in text
    assert "Andere Crew" not in text

    response = utils.get_ok(
        utils.get_url(
            "user.organization_invitation_negotiate",
            organization_invitation_id=invitation_id,
        )
    )
    assert "Meine Crew" in _text(utils, response)


def test_user_cannot_negotiate_foreign_invitation(seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_user("new@member.de")
    utils.login("new@member.de")
    invitation_id = seeder.create_admin_unit_invitation(
        admin_unit_id, "someone@else.de"
    )

    utils.get_unauthorized(
        utils.get_url(
            "user.organization_invitation_negotiate",
            organization_invitation_id=invitation_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "user.organization_invitation_negotiate",
                organization_invitation_id=4711,
            )
        )
    )


def test_invitation_link_of_unknown_invitation(seeder, utils):
    seeder.setup_base()

    utils.assert_response_notFound(
        utils.get(utils.get_url("main.user_organization_invitation", id=4711))
    )
    utils.assert_response_notFound(
        utils.get(utils.get_url("manage.organization_create", invitation_id=4711))
    )
