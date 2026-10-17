"""SqlAlchemyOrganizationAdminReadRepository against the database."""

from project.application.queries import ListOrganizationsForAdminQuery


def test_list_and_get(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    alpha_id = seeder.create_admin_unit(seeder.create_user("a@test.de"), "alpha")

    with app.app_context():
        repo = app.container.read_repos.organization_admin_read_repo()

        with app.container.infrastructure.read_session_scope():
            page = repo.list(ListOrganizationsForAdminQuery())
            found = repo.list(ListOrganizationsForAdminQuery(keyword="alp"))
            mine = repo.get(admin_unit_id)
            alpha = repo.get(alpha_id)
            missing = repo.get(4711)

    names = [item.name for item in page.items]
    assert names.index("alpha") < names.index("Meine Crew")
    assert [item.id for item in found.items] == [alpha_id]
    assert mine.is_verified is True
    assert alpha.is_verified is False
    assert alpha.can_invite_other is True
    assert alpha.created_at is not None
    assert missing is None
