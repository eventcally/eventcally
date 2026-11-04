"""SqlAlchemyUserProfileReadRepository against the database."""

from project.infrastructure.models import User


def _get(app, user_id):
    with app.app_context():
        repo = app.container.read_repos.user_profile_read_repo()

        with app.container.infrastructure.read_session_scope():
            return repo.get_profile(user_id)


def test_the_profile_of_a_user(app, db, seeder):
    user_id = seeder.create_user("p@test.de")
    with app.app_context():
        user = db.session.get(User, user_id)
        user.locale = "de"
        user.newsletter_enabled = True
        db.session.commit()

    profile = _get(app, user_id)

    assert profile.email == "p@test.de"
    assert profile.locale == "de"
    assert profile.newsletter_enabled is True
    assert profile.deletion_requested_at is None


def test_an_unknown_user_is_none(app, db):
    assert _get(app, 4711) is None
