from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import joinedload, undefer_group

from project.application.queries.list_organization_invitations_query import (
    ListOrganizationInvitationsQuery,
    OrganizationInvitationSort,
)
from project.application.queries.list_user_organization_invitations_query import (
    ListUserOrganizationInvitationsQuery,
)
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationDetailReadModel,
    OrganizationInvitationListItemReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_invitation_read_repository import (
    AbstractOrganizationInvitationReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
)
from project.models import AdminUnit, AdminUnitInvitation, User

# Every ordering ends with the id, which is also the default order.
_SORT_ORDER = {
    None: [],
    OrganizationInvitationSort.created_at_desc: [AdminUnitInvitation.created_at.desc()],
    OrganizationInvitationSort.updated_at_desc: [
        AdminUnitInvitation.updated_at.desc().nulls_last()
    ],
    OrganizationInvitationSort.last_modified_at_desc: [
        AdminUnitInvitation.last_modified_at.desc()
    ],
}


class SqlAlchemyOrganizationInvitationReadRepository(
    AbstractOrganizationInvitationReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list(
        self, query: ListOrganizationInvitationsQuery
    ) -> Page[OrganizationInvitationListItemReadModel]:
        filters = [
            AdminUnitInvitation.admin_unit_id == query.admin_unit_id,
            *trackable_filters(AdminUnitInvitation, query.trackable),
        ]
        order_by = [*_SORT_ORDER[query.sort], AdminUnitInvitation.id]

        stmt = (
            select(AdminUnitInvitation)
            .where(*filters)
            .options(undefer_group("trackable"))
            .order_by(*order_by)
        )
        count_stmt = select(AdminUnitInvitation.id).where(*filters)

        return paginate(self.session, stmt, count_stmt, query.page, _to_list_item)

    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationInvitationDetailReadModel]:
        stmt = (
            select(AdminUnitInvitation)
            .where(AdminUnitInvitation.id == object_id)
            .options(
                *audit_options(AdminUnitInvitation),
                joinedload(AdminUnitInvitation.admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                ),
            )
        )
        invitation = self.session.execute(stmt).scalar_one_or_none()

        if invitation is None:
            return None

        return _to_detail(invitation).model_copy(
            update={"audit": to_audit_read_model(invitation)}
        )

    def list_for_user(
        self, query: ListUserOrganizationInvitationsQuery
    ) -> Page[OrganizationInvitationDetailReadModel]:
        user_email = (
            select(User.email).where(User.id == query.user_id).scalar_subquery()
        )
        filters = [
            func.lower(AdminUnitInvitation.email) == func.lower(user_email),
            *trackable_filters(AdminUnitInvitation, query.trackable),
        ]
        stmt = (
            select(AdminUnitInvitation)
            .where(*filters)
            .options(
                undefer_group("trackable"),
                joinedload(AdminUnitInvitation.admin_unit).load_only(
                    AdminUnit.id, AdminUnit.name
                ),
            )
            .order_by(*_SORT_ORDER[query.sort], AdminUnitInvitation.id)
        )
        count_stmt = select(AdminUnitInvitation.id).where(*filters)

        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_detail(row[0])
        )

    def get_recipient_email(self, object_id: ObjectId) -> Optional[str]:
        return self.session.execute(
            select(AdminUnitInvitation.email).where(AdminUnitInvitation.id == object_id)
        ).scalar_one_or_none()


def _to_list_item(row) -> OrganizationInvitationListItemReadModel:
    invitation = row[0]

    return OrganizationInvitationListItemReadModel(
        id=invitation.id,
        email=invitation.email,
        admin_unit_name=invitation.admin_unit_name,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        last_modified_at=invitation.last_modified_at,
    )


def _to_detail(invitation) -> OrganizationInvitationDetailReadModel:
    return OrganizationInvitationDetailReadModel(
        id=invitation.id,
        email=invitation.email,
        admin_unit_id=invitation.admin_unit_id,
        admin_unit_name=invitation.admin_unit_name,
        relation_auto_verify_event_reference_requests=(
            invitation.relation_auto_verify_event_reference_requests
        ),
        relation_verify=invitation.relation_verify,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        last_modified_at=invitation.last_modified_at,
        admin_unit=OrganizationRefReadModel(
            id=invitation.admin_unit.id, name=invitation.admin_unit.name
        ),
    )
