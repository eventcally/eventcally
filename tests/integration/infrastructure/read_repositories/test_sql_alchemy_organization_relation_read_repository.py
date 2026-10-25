"""SqlAlchemyOrganizationRelationReadRepository against the database."""

from sqlalchemy import text

from project.application.queries import (
    ListOutgoingOrganizationRelationsQuery,
    OrganizationRelationSort,
)


def test_list_filters_sort_and_get(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    alpha_id = seeder.create_admin_unit(seeder.create_user("a@test.de"), "alpha Crew")
    beta_id = seeder.create_admin_unit(seeder.create_user("b@test.de"), "Beta Crew")
    alpha_rel = seeder.create_admin_unit_relation(admin_unit_id, alpha_id, verify=True)
    beta_rel = seeder.create_admin_unit_relation(
        admin_unit_id, beta_id, auto_verify_event_reference_requests=True
    )

    with app.app_context():
        db.session.execute(
            text("UPDATE adminunit SET updated_at = '2030-01-01' WHERE id = :id"),
            {"id": beta_id},
        )
        db.session.commit()

        repo = app.container.read_repos.organization_relation_read_repo()

        def ids(**kwargs):
            with app.container.infrastructure.read_session_scope():
                page = repo.list(
                    ListOutgoingOrganizationRelationsQuery(
                        admin_unit_id=admin_unit_id, **kwargs
                    )
                )
                return [item.id for item in page.items]

        assert ids() == [alpha_rel, beta_rel]
        assert ids(sort=OrganizationRelationSort.last_modified_at_desc) == [
            beta_rel,
            alpha_rel,
        ]
        assert ids(keyword="BE") == [beta_rel]
        assert ids(verify=True) == [alpha_rel]
        assert ids(auto_verify_event_reference_requests=False) == [alpha_rel]

        with app.container.infrastructure.read_session_scope():
            relation = repo.get(beta_rel)
            missing = repo.get(4711)

    assert relation.auto_verify_event_reference_requests is True
    assert relation.verify is False
    assert relation.target_admin_unit.name == "Beta Crew"
    assert relation.source_admin_unit_id == admin_unit_id
    assert missing is None


def test_organization_exists_and_get_by_target(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_id = seeder.create_admin_unit(seeder.create_user("a@test.de"), "Alpha Crew")
    relation_id = seeder.create_admin_unit_relation(admin_unit_id, other_id)

    with app.app_context():
        repo = app.container.read_repos.organization_relation_read_repo()

        with app.container.infrastructure.read_session_scope():
            exists = repo.organization_exists(admin_unit_id)
            missing_organization = repo.organization_exists(4711)
            relation = repo.get_by_target(admin_unit_id, other_id)
            missing_relation = repo.get_by_target(other_id, admin_unit_id)

    assert exists is True
    assert missing_organization is False
    assert relation.id == relation_id
    assert relation.target_admin_unit.name == "Alpha Crew"
    assert missing_relation is None
