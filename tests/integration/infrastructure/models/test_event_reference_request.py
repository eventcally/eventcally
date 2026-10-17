def test_rejection_reason_zero_is_normalized_to_none(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = EventReferenceRequest()
        reference_request.event_id = event_id
        reference_request.admin_unit_id = other_admin_unit_id
        reference_request.review_status = EventReferenceRequestReviewStatus.rejected
        reference_request.rejection_reason = 0
        db.session.add(reference_request)
        db.session.commit()

        assert reference_request.rejection_reason is None
