from project.infrastructure.actor import Actor


def test_current_user_id_is_none_without_login(app):
    with app.test_request_context():
        assert Actor.current_user_id_or_none() is None


def test_current_user_id_of_authenticated_user(app, mocker):
    mocker.patch(
        "project.infrastructure.actor.current_user",
        mocker.Mock(is_authenticated=True, id=42),
    )

    assert Actor.current_user_id_or_none() == 42


def test_current_app_installation_id(app, mocker):
    with app.test_request_context():
        assert Actor.current_app_installation_id_or_none() is None

    mocker.patch(
        "project.infrastructure.actor.current_token",
        mocker.Mock(app_installation_id=7),
    )

    assert Actor.current_app_installation_id_or_none() == 7
