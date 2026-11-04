def test_create_is_a_shell(client, utils, seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.organization_invitation_create", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_update_is_a_shell(client, utils, seeder):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.get_endpoint_ok(
        "manage_admin_unit.organization_invitation_update",
        id=admin_unit_id,
        organization_invitation_id=invitation_id,
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_update_of_unknown_or_foreign_invitation(client, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.organization_invitation_update",
                id=admin_unit_id,
                organization_invitation_id=4711,
            )
        )
    )
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.organization_invitation_update",
            id=other_admin_unit_id,
            organization_invitation_id=invitation_id,
        )
    )


def test_delete_page_is_gone(client, utils, seeder):
    """Revoking is a modal of the list."""
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    utils.assert_response_notFound(
        utils.get(
            f"/manage/admin_unit/{admin_unit_id}/organization_invitation/{invitation_id}/delete"
        )
    )
