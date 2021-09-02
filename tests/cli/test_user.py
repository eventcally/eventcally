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


def test_create(client, seeder, app):
    with app.app_context():
        from project.services.user import find_user_by_email

        user = find_user_by_email("test@test.de")
        assert not user

    runner = app.test_cli_runner()
    result = runner.invoke(
        args=["user", "create", "test@test.de", "password", "--confirm", "--admin"]
    )
    assert "user_id" in result.output

    with app.app_context():
        from project.services.user import find_user_by_email

        user = find_user_by_email("test@test.de")
        assert user.confirmed_at is not None


def test_confirm(client, seeder, app):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["user", "create", "test@test.de", "password"])

    with app.app_context():
        from project.services.user import find_user_by_email

        user = find_user_by_email("test@test.de")
        assert user.confirmed_at is None

    result = runner.invoke(args=["user", "confirm", "test@test.de"])
    assert "Confirmed user test@test.de." in result.output

    with app.app_context():
        from project.services.user import find_user_by_email

        user = find_user_by_email("test@test.de")
        assert user.confirmed_at is not None
