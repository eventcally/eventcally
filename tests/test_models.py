def test_location_update_coordinate(client, app, db):
    from project.models import Location

    location = Location()
    location.latitude = 51.9077888
    location.longitude = 10.4333312
    location.update_coordinate()

    assert location.coordinate is not None


def test_event_category(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event

        event = Event.query.get(event_id)
        event.categories = []
        db.session.commit()

        assert event.category is None


def test_oauth2_token(client, app):
    from project.models import OAuth2Token

    token = OAuth2Token()
    token.revoked = True
    assert not token.is_refresh_token_active()

    token.revoked = False
    token.issued_at = 0
    token.expires_in = 0
    assert not token.is_refresh_token_active()


def test_admin_unit_relations(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    with app.app_context():
        from project.services.admin_unit import get_admin_unit_by_id

        admin_unit = get_admin_unit_by_id(admin_unit_id)
        assert len(admin_unit.outgoing_relations) == 1
        relation = admin_unit.outgoing_relations[0]
        assert relation.id == relation_id

        db.session.delete(relation)
        db.session.commit()
        assert len(admin_unit.outgoing_relations) == 0


def test_admin_unit_deletion(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    my_event_id = seeder.create_event(admin_unit_id)
    suggestion_id = seeder.create_event_suggestion(admin_unit_id)
    event_place_id = seeder.upsert_default_event_place(admin_unit_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    invitation_id = seeder.create_invitation(admin_unit_id, "newbie@domain.com")

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    other_event_id = seeder.create_event(other_admin_unit_id)
    incoming_reference_request_id = seeder.create_reference_request(
        other_event_id, admin_unit_id
    )
    outgoing_reference_request_id = seeder.create_reference_request(
        my_event_id, other_admin_unit_id
    )
    incoming_relation_id = seeder.create_admin_unit_relation(
        other_admin_unit_id, admin_unit_id
    )
    outgoing_relation_id = seeder.create_admin_unit_relation(
        admin_unit_id, other_admin_unit_id
    )
    incoming_reference_id = seeder.create_reference(other_event_id, admin_unit_id)
    outgoing_reference_id = seeder.create_reference(my_event_id, other_admin_unit_id)

    with app.app_context():
        from project.models import (
            AdminUnit,
            AdminUnitMemberInvitation,
            AdminUnitRelation,
            Event,
            EventOrganizer,
            EventPlace,
            EventReference,
            EventReferenceRequest,
            EventSuggestion,
        )
        from project.services.admin_unit import get_admin_unit_by_id

        admin_unit = get_admin_unit_by_id(admin_unit_id)
        other_admin_unit = get_admin_unit_by_id(other_admin_unit_id)

        db.session.delete(admin_unit)
        db.session.commit()
        assert len(other_admin_unit.outgoing_relations) == 0

        assert Event.query.get(my_event_id) is None
        assert AdminUnitRelation.query.get(incoming_relation_id) is None
        assert AdminUnitRelation.query.get(outgoing_relation_id) is None
        assert EventReference.query.get(incoming_reference_id) is None
        assert EventReference.query.get(outgoing_reference_id) is None
        assert EventReferenceRequest.query.get(incoming_reference_request_id) is None
        assert EventReferenceRequest.query.get(outgoing_reference_request_id) is None
        assert EventSuggestion.query.get(suggestion_id) is None
        assert EventPlace.query.get(event_place_id) is None
        assert EventOrganizer.query.get(organizer_id) is None
        assert AdminUnitMemberInvitation.query.get(invitation_id) is None

        assert AdminUnit.query.get(other_admin_unit_id) is not None
        assert Event.query.get(other_event_id) is not None
