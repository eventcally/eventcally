from project.models import AdminUnitRelation
from project.repos.base_repo import BaseRepo


class OrganizationRelationRepo(BaseRepo[AdminUnitRelation]):
    model_class = AdminUnitRelation

    def create_relation(
        self, source_organization_id, target_organization_id, verify=False
    ) -> AdminUnitRelation:
        relation = AdminUnitRelation(
            source_admin_unit_id=source_organization_id,
            target_admin_unit_id=target_organization_id,
            verify=verify,
        )
        self.insert_object(relation)
        return relation

    def get_relation(
        self, source_organization_id, target_organization_id
    ) -> AdminUnitRelation:
        return (
            self.db.session.query(AdminUnitRelation)
            .filter(
                AdminUnitRelation.source_admin_unit_id == source_organization_id,
                AdminUnitRelation.target_admin_unit_id == target_organization_id,
            )
            .first()
        )
