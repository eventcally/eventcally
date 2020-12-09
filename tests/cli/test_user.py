def test_add_admin_roles(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        from project.services.user import get_user

        user = get_user(user_id)
        assert not user.has_role("admin")

    runner = app.test_cli_runner()
    result = runner.invoke(args=["user", "add-admin-roles", "test@test.de"])
    assert "Admin roles were added to test@test.de." in result.output

    with app.app_context():
        from project.services.user import get_user

        user = get_user(user_id)
        is_admin = user.has_role("admin")
        assert is_admin


def test_add_admin_roles_UserDoesNotExist(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()

    runner = app.test_cli_runner()
    result = runner.invoke(args=["user", "add-admin-roles", "unknown@test.de"])
    assert result.exit_code == 1
    assert "User with given email does not exist." in result.exception.args[0]
