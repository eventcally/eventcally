def test_update_organization_relation_sets_verify_and_auto_verify(
    client, app, db, seeder
):
    _, source_admin_unit_id = seeder.setup_base(
        log_in=False, email="uor-source@test.de", name="UOR Source Unit"
    )
    _, target_admin_unit_id = seeder.setup_base(
        log_in=False, email="uor-target@test.de", name="UOR Target Unit"
    )

    with app.app_context():
        from flask import current_app

        from project.services.admin_unit import get_admin_unit_relation

        organization_service = current_app.container.services.organization_service()

        relation = organization_service.update_organization_relation(
            source_admin_unit_id,
            target_admin_unit_id,
            verify=True,
            auto_verify_event_reference_requests=True,
        )

        assert relation.verify is True
        assert relation.auto_verify_event_reference_requests is True

        loaded = get_admin_unit_relation(source_admin_unit_id, target_admin_unit_id)
        assert loaded is not None
        assert loaded.verify is True
        assert loaded.auto_verify_event_reference_requests is True

        # explicitly unsetting verify (False, not None) updates it back
        relation = organization_service.update_organization_relation(
            source_admin_unit_id,
            target_admin_unit_id,
            verify=False,
        )
        assert relation.verify is False
        # auto_verify_event_reference_requests untouched (arg omitted -> None)
        assert relation.auto_verify_event_reference_requests is True
