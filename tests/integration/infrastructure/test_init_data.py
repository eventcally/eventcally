def test_create_initial_data_syncs_organization_admin_permissions(app, db):
    from project.infrastructure.init_data import (
        create_initial_data,
        organization_admin_permissions,
        organization_event_expert_permissions,
    )
    from project.infrastructure.models import AdminUnitMemberRole

    with app.app_context():
        role = AdminUnitMemberRole.query.filter_by(name="admin").first()
        role.permissions = ["apps:read"]
        db.session.commit()

        create_initial_data()

        role = AdminUnitMemberRole.query.filter_by(name="admin").first()
        assert role.permissions == organization_admin_permissions
        assert "webhook_deliveries:read" in role.permissions
        assert "webhook_delivery_attempts:write" in role.permissions

        expert = AdminUnitMemberRole.query.filter_by(name="event_verifier").first()
        assert not any(p.startswith("webhook_") for p in expert.permissions)
        assert expert.permissions == organization_event_expert_permissions
