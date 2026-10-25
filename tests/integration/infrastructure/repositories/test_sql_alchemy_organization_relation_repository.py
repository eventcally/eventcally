from project.domain.events.organization_invitation_accepted import (
    OrganizationInvitationAccepted,
)
from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)
from project.domain.models.entities.actor import Actor
from project.infrastructure.repositories.sql_alchemy_organization_relation_repository import (
    SqlAlchemyOrganizationRelationRepository,
)


def test_add_with_accepted_invitation_sets_event_id(app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    with app.app_context():
        repo = SqlAlchemyOrganizationRelationRepository(db.session)
        relation = OrganizationRelationAggregate.create(
            actor=Actor(user_id=user_id),
            source_admin_unit_id=admin_unit_id,
            target_admin_unit_id=other_admin_unit_id,
            invited=True,
            accepted_invitation_email="other@test.de",
            target_admin_unit_name="Other Crew",
        )

        repo.add(relation)
        db.session.commit()

        accepted = relation.get_first_domain_event_by_type(
            OrganizationInvitationAccepted
        )
        assert accepted.id == relation.id
        loaded = repo.get(relation.id)
        assert loaded.invited is True
        assert loaded.source_admin_unit_id == admin_unit_id
