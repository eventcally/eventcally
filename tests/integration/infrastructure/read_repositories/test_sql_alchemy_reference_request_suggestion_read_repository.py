"""SqlAlchemyReferenceRequestSuggestionReadRepository against the database."""


def test_sources_order_filter_and_limit(app, db, seeder):
    from project.infrastructure.models import AdminUnit

    _, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    ids = {
        name: seeder.create_admin_unit(other_user_id, name)
        for name in ["R1", "R2", "F1", "F2", "S1", "S2", "Closed"]
    }
    with app.app_context():
        db.session.get(AdminUnit, ids["Closed"]).incoming_reference_requests_allowed = (
            False
        )
        db.session.commit()
    event_id = seeder.create_event(admin_unit_id)
    for name in ["R1", "R2", "Closed"]:
        seeder.create_reference_request(event_id, ids[name])
    for name in ["F1", "F2", "Closed"]:
        seeder.create_reference(event_id, ids[name])
    seeder.create_admin_unit_relation(ids["S1"], admin_unit_id, verify=True)
    seeder.create_admin_unit_relation(
        ids["S2"], admin_unit_id, auto_verify_event_reference_requests=True
    )
    # Relations toward another admin unit and requests of other events do not count.
    seeder.create_admin_unit_relation(admin_unit_id, ids["R1"], verify=True)
    seeder.create_reference_request(seeder.create_event(ids["F1"]), ids["R1"])

    with app.app_context():
        repo = app.container.read_repos.reference_request_suggestion_read_repo()

        def names(method, limit=10):
            with app.container.infrastructure.read_session_scope():
                return [o.name for o in getattr(repo, method)(admin_unit_id, limit)]

        assert names("newest_requested_organizations") == ["R2", "R1"]
        assert names("newest_requested_organizations", 1) == ["R2"]
        assert names("newest_referencing_organizations") == ["F2", "F1"]
        # The verified seed admin unit is related through "eventcally", the verifier.
        assert names("related_organizations")[:2] == ["S2", "S1"]
        assert set(names("related_organizations")) == {"S2", "S1", "eventcally"}
        others = names("other_organizations")
        assert "Closed" not in others
        assert "Meine Crew" not in others
        assert {"R1", "R2", "F1", "F2", "S1", "S2"} <= set(others)
        assert len(names("other_organizations", 2)) == 2
