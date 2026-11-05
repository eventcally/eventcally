from project.application.queries import GetEventDetailQuery


def _event(app, event_id):
    return app.container.cqrs.query_bus().handle(GetEventDetailQuery(id=event_id))


def test_rights_of_an_anonymous_visitor_are_all_false(app, seeder):
    from project.presentation.shared.event_rights import event_user_rights

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.test_request_context():
        rights = event_user_rights(_event(app, event_id))

    assert rights
    assert not any(rights.values())


def test_rights_of_the_owner(app, client, seeder):
    from flask_login import login_user

    from project.infrastructure.user_datastore import get_user
    from project.presentation.shared.event_rights import event_user_rights

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with app.test_request_context():
        login_user(get_user(user_id))
        rights = event_user_rights(_event(app, event_id))

    assert rights["can_update_event"]
    assert rights["can_duplicate_event"]
    assert rights["can_create_event"]
    assert rights["can_view_actions"]
    assert not rights["can_reference_event"]
