"""SqlAlchemyUserAdminReadRepository against the database."""

from project.application.queries import PageRequest


def _call(app, method, *args):
    with app.app_context():
        repo = app.container.read_repos.user_admin_read_repo()

        with app.container.infrastructure.read_session_scope():
            return getattr(repo, method)(*args)


def test_users_by_email_with_their_roles(app, db, seeder):
    seeder.create_user("b@test.de")
    seeder.create_user("A@test.de", admin=True)

    page = _call(app, "list_users", PageRequest(per_page=1))

    assert [u.email for u in page.items] == ["A@test.de"]
    assert page.total == 2
    assert page.has_next
    assert page.items[0].roles == ["admin"]
    assert page.items[0].confirmed_at is not None


def test_a_user_and_the_roles(app, db, seeder):
    user_id = seeder.create_user("b@test.de")

    assert _call(app, "get_user", user_id).email == "b@test.de"
    assert _call(app, "get_user", 4711) is None
    assert [r.name for r in _call(app, "list_roles")] == ["admin"] or _call(
        app, "list_roles"
    ) == []


def test_newsletter_recipients_are_confirmed_and_opted_in(app, db, seeder):
    from project.infrastructure.models import User

    seeder.create_user("in@test.de")
    seeder.create_user("unconfirmed@test.de", confirm=False)
    seeder.create_user("out@test.de")

    with app.app_context():
        for user in User.query.all():
            user.newsletter_enabled = user.email == "in@test.de" or (
                user.email == "unconfirmed@test.de"
            )
        db.session.commit()

    recipients = _call(app, "list_newsletter_recipients")

    assert [r.email for r in recipients] == ["in@test.de"]
