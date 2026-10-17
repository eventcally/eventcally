from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import undefer_group

from project.application.queries.list_organizations_for_admin_query import (
    ListOrganizationsForAdminQuery,
)
from project.application.read_models.organization_admin_read_models import (
    OrganizationAdminReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_admin_read_repository import (
    AbstractOrganizationAdminReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import AdminUnit
from project.infrastructure.read_repositories.query_helpers import paginate
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
)
from project.utils import parse_like_term


def _select():
    return select(AdminUnit, AdminUnit.is_verified).options(undefer_group("trackable"))


class SqlAlchemyOrganizationAdminReadRepository(
    AbstractOrganizationAdminReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def list(
        self, query: ListOrganizationsForAdminQuery
    ) -> Page[OrganizationAdminReadModel]:
        filters = []

        if query.keyword:
            filters.append(AdminUnit.name.ilike(parse_like_term(query.keyword)))

        stmt = (
            _select().where(*filters).order_by(func.lower(AdminUnit.name), AdminUnit.id)
        )
        count_stmt = select(AdminUnit.id).where(*filters)
        return paginate(self.session, stmt, count_stmt, query.page, _to_model)

    def get(self, object_id: ObjectId) -> Optional[OrganizationAdminReadModel]:
        row = self.session.execute(
            _select()
            .where(AdminUnit.id == object_id)
            .options(*audit_options(AdminUnit))
        ).one_or_none()

        if row is None:
            return None

        return _to_model(row).model_copy(update={"audit": to_audit_read_model(row[0])})


def _to_model(row) -> OrganizationAdminReadModel:
    admin_unit, is_verified = row

    return OrganizationAdminReadModel(
        id=admin_unit.id,
        name=admin_unit.name,
        is_verified=bool(is_verified),
        created_at=admin_unit.created_at,
        deletion_requested_at=admin_unit.deletion_requested_at,
        incoming_reference_requests_allowed=bool(
            admin_unit.incoming_reference_requests_allowed
        ),
        can_create_other=bool(admin_unit.can_create_other),
        can_invite_other=bool(admin_unit.can_invite_other),
        can_verify_other=bool(admin_unit.can_verify_other),
    )
