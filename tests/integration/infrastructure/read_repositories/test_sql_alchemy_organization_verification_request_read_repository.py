"""SqlAlchemyOrganizationVerificationRequestReadRepository against the database."""

from sqlalchemy import text

from project.application.queries import (
    ListIncomingOrganizationVerificationRequestsQuery,
    ListOutgoingOrganizationVerificationRequestsQuery,
)
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)


def test_lists_and_get(app, db, seeder):
    _, target_id = seeder.setup_base(log_in=False)
    alpha_user_id = seeder.create_user("alpha@test.de")
    alpha_id = seeder.create_admin_unit(alpha_user_id, "Alpha", verified=False)
    beta_user_id = seeder.create_user("beta@test.de")
    beta_id = seeder.create_admin_unit(beta_user_id, "Beta", verified=False)
    old_id = seeder.create_admin_unit_verification_request(alpha_id, target_id)
    new_id = seeder.create_admin_unit_verification_request(beta_id, target_id)

    with app.app_context():
        db.session.execute(
            text(
                "UPDATE adminunitverificationrequest SET created_at = '2026-01-01',"
                " review_status = 3, rejection_reason = 2 WHERE id = :id"
            ),
            {"id": old_id},
        )
        db.session.commit()

        repo = app.container.read_repos.organization_verification_request_read_repo()
        with app.container.infrastructure.read_session_scope():
            incoming = repo.list_incoming(
                ListIncomingOrganizationVerificationRequestsQuery(
                    admin_unit_id=target_id
                )
            )
            rejected = repo.list_incoming(
                ListIncomingOrganizationVerificationRequestsQuery(
                    admin_unit_id=target_id,
                    review_status=OrganizationVerificationRequestReviewStatus.rejected,
                )
            )
            outgoing = repo.list_outgoing(
                ListOutgoingOrganizationVerificationRequestsQuery(
                    admin_unit_id=alpha_id
                )
            )
            old = repo.get(old_id)
            missing = repo.get(4711)
            exists = repo.organization_exists(target_id)

    assert [item.id for item in incoming.items] == [new_id, old_id]
    assert [item.id for item in rejected.items] == [old_id]
    assert [item.id for item in outgoing.items] == [old_id]
    assert old.rejection_reason == (
        OrganizationVerificationRequestRejectionReason.missinginformation
    )
    assert old.source_admin_unit.name == "Alpha"
    assert old.target_admin_unit.id == target_id
    assert missing is None
    assert exists is True


def test_get_review(app, db, seeder):
    _, target_id = seeder.setup_base(log_in=False)
    source_user_id = seeder.create_user("source@test.de")
    source_id = seeder.create_admin_unit(source_user_id, "Quelle", verified=False)
    seeder.create_admin_unit_member(source_id, ["event_verifier"], "m@test.de")
    request_id = seeder.create_admin_unit_verification_request(source_id, target_id)

    with app.app_context():
        repo = app.container.read_repos.organization_verification_request_read_repo()

        with app.container.infrastructure.read_session_scope():
            review = repo.get_review(request_id)
            missing = repo.get_review(4711)

    assert review.target_admin_unit_id == target_id
    assert review.source_admin_unit.name == "Quelle"
    assert review.source_admin_unit.is_verified is False
    assert review.source_admin_unit.location.postalCode == "12345"
    assert [m.user.email for m in review.source_admin_unit.members] == [
        "source@test.de",
        "m@test.de",
    ]
    assert [r.name for r in review.source_admin_unit.members[1].roles] == [
        "event_verifier"
    ]
    assert missing is None
