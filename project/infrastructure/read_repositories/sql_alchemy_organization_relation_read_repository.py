from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import aliased, contains_eager, joinedload, undefer_group

from project.application.queries.list_outgoing_organization_relations_query import (
    ListOutgoingOrganizationRelationsQuery,
)
from project.application.queries.organization_relation_sort import (
    OrganizationRelationSort,
)
from project.application.read_models.organization_relation_read_models import (
    OrganizationRelationReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_relation_read_repository import (
    AbstractOrganizationRelationReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit, AdminUnitRelation
from project.infrastructure.read_repositories.query_helpers import paginate
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
    to_organization_ref_read_model,
)
from project.utils import parse_like_term

SourceAdminUnit = aliased(AdminUnit)
_load_source = joinedload(
    AdminUnitRelation.source_admin_unit.of_type(SourceAdminUnit)
).load_only(SourceAdminUnit.id, SourceAdminUnit.name)


# No sort (the API, an unknown form key) keeps the legacy id order.
_SORT_ORDER = {
    None: [],
    OrganizationRelationSort.name: [func.lower(AdminUnit.name)],
    OrganizationRelationSort.last_modified_at_desc: [AdminUnit.last_modified_at.desc()],
}


class SqlAlchemyOrganizationRelationReadRepository(
    AbstractOrganizationRelationReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: ListOutgoingOrganizationRelationsQuery
    ) -> Page[OrganizationRelationReadModel]:
        filters = [AdminUnitRelation.source_admin_unit_id == query.admin_unit_id]

        if query.keyword:
            filters.append(AdminUnit.name.ilike(parse_like_term(query.keyword)))

        if query.verify is not None:
            filters.append(AdminUnitRelation.verify.is_(query.verify))

        if query.auto_verify_event_reference_requests is not None:
            filters.append(
                AdminUnitRelation.auto_verify_event_reference_requests.is_(
                    query.auto_verify_event_reference_requests
                )
            )

        stmt = (
            select(AdminUnitRelation)
            .join(AdminUnit, AdminUnitRelation.target_admin_unit_id == AdminUnit.id)
            .where(*filters)
            .options(
                undefer_group("trackable"),
                contains_eager(AdminUnitRelation.target_admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                ),
                _load_source,
            )
            .order_by(*_SORT_ORDER[query.sort], AdminUnitRelation.id)
        )
        count_stmt = (
            select(AdminUnitRelation.id)
            .join(AdminUnit, AdminUnitRelation.target_admin_unit_id == AdminUnit.id)
            .where(*filters)
        )
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )

    def get(self, object_id: ObjectId) -> Optional[OrganizationRelationReadModel]:
        relation = self.session.execute(
            select(AdminUnitRelation)
            .where(AdminUnitRelation.id == object_id)
            .options(
                *audit_options(AdminUnitRelation),
                joinedload(AdminUnitRelation.target_admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                ),
                _load_source,
            )
        ).scalar_one_or_none()
        return (
            _to_model(relation).model_copy(
                update={"audit": to_audit_read_model(relation)}
            )
            if relation
            else None
        )

    def get_by_target(
        self, admin_unit_id: ObjectId, target_admin_unit_id: ObjectId
    ) -> Optional[OrganizationRelationReadModel]:
        relation_id = self.session.execute(
            select(AdminUnitRelation.id).where(
                AdminUnitRelation.source_admin_unit_id == admin_unit_id,
                AdminUnitRelation.target_admin_unit_id == target_admin_unit_id,
            )
        ).scalar_one_or_none()
        return self.get(relation_id) if relation_id else None


def _to_model(relation) -> OrganizationRelationReadModel:
    return OrganizationRelationReadModel(
        id=relation.id,
        source_admin_unit_id=relation.source_admin_unit_id,
        target_admin_unit_id=relation.target_admin_unit_id,
        verify=bool(relation.verify),
        auto_verify_event_reference_requests=bool(
            relation.auto_verify_event_reference_requests
        ),
        created_at=relation.created_at,
        updated_at=relation.updated_at,
        last_modified_at=relation.last_modified_at,
        source_admin_unit=to_organization_ref_read_model(relation.source_admin_unit),
        target_admin_unit=to_organization_ref_read_model(relation.target_admin_unit),
    )
