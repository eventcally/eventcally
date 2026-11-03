"""Parity of the invited user's organization invitation pages. Written against the
ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def test_invitation_link_of_unknown_invitation(seeder, utils):
    seeder.setup_base()

    utils.assert_response_notFound(
        utils.get(utils.get_url("main.user_organization_invitation", id=4711))
    )
    utils.assert_response_notFound(
        utils.get(utils.get_url("manage.organization_create", invitation_id=4711))
    )
