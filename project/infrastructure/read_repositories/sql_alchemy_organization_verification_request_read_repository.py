from typing import Optional

from sqlalchemy import exists, select
from sqlalchemy.orm import joinedload, selectinload, undefer, undefer_group

from project.application.queries.list_incoming_organization_verification_requests_query import (
    ListIncomingOrganizationVerificationRequestsQuery,
)
from project.application.queries.list_outgoing_organization_verification_requests_query import (
    ListOutgoingOrganizationVerificationRequestsQuery,
)
from project.application.read_models.organization_verification_request_read_models import (
    OrganizationVerificationRequestReadModel,
    OrganizationVerificationRequestReviewReadModel,
    VerificationReviewOrganizationReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_verification_request_read_repository import (
    AbstractOrganizationVerificationRequestReadRepository,
)
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.models import (
    AdminUnit,
    AdminUnitMember,
    AdminUnitVerificationRequest,
    Image,
    User,
)
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
    trackable_order,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    audit_options,
    to_audit_read_model,
    to_image_read_model,
    to_location_read_model,
    to_organization_member_read_model,
    to_organization_ref_read_model,
)

_options = [
    undefer_group("trackable"),
    joinedload(AdminUnitVerificationRequest.source_admin_unit).load_only(
        AdminUnit.id, AdminUnit.name
    ),
    joinedload(AdminUnitVerificationRequest.target_admin_unit).load_only(
        AdminUnit.id, AdminUnit.name
    ),
]


class SqlAlchemyOrganizationVerificationRequestReadRepository(
    AbstractOrganizationVerificationRequestReadRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def organization_exists(self, admin_unit_id: ObjectId) -> bool:
        return self.session.execute(
            select(exists().where(AdminUnit.id == admin_unit_id))
        ).scalar_one()

    def list_incoming(
        self, query: ListIncomingOrganizationVerificationRequestsQuery
    ) -> Page[OrganizationVerificationRequestReadModel]:
        filters = [
            AdminUnitVerificationRequest.target_admin_unit_id == query.admin_unit_id
        ]

        if query.review_status is not None:
            filters.append(
                AdminUnitVerificationRequest.review_status == int(query.review_status)
            )

        return self._list(filters, query)

    def list_outgoing(
        self, query: ListOutgoingOrganizationVerificationRequestsQuery
    ) -> Page[OrganizationVerificationRequestReadModel]:
        return self._list(
            [AdminUnitVerificationRequest.source_admin_unit_id == query.admin_unit_id],
            query,
        )

    def get(
        self, object_id: ObjectId
    ) -> Optional[OrganizationVerificationRequestReadModel]:
        request = self.session.execute(
            select(AdminUnitVerificationRequest)
            .where(AdminUnitVerificationRequest.id == object_id)
            .options(*_options, *audit_options(AdminUnitVerificationRequest))
        ).scalar_one_or_none()
        return (
            _to_model(request).model_copy(
                update={"audit": to_audit_read_model(request)}
            )
            if request
            else None
        )

    def get_review(
        self, object_id: ObjectId
    ) -> Optional[OrganizationVerificationRequestReviewReadModel]:
        request = self.session.execute(
            select(AdminUnitVerificationRequest)
            .where(AdminUnitVerificationRequest.id == object_id)
            .options(
                joinedload(AdminUnitVerificationRequest.source_admin_unit).options(
                    undefer_group("trackable"),
                    undefer_group("detail"),
                    joinedload(AdminUnit.location),
                    joinedload(AdminUnit.logo).options(
                        undefer(Image.created_at),
                        undefer(Image.updated_at),
                        joinedload(Image.license),
                    ),
                )
            )
        ).scalar_one_or_none()

        if request is None:
            return None

        source = request.source_admin_unit
        is_verified = self.session.execute(
            select(AdminUnit.is_verified).where(AdminUnit.id == source.id)
        ).scalar_one()
        members = self.session.execute(
            select(AdminUnitMember)
            .where(AdminUnitMember.admin_unit_id == source.id)
            .options(
                joinedload(AdminUnitMember.user).load_only(User.id, User.email),
                selectinload(AdminUnitMember.roles),
            )
            .order_by(AdminUnitMember.id)
        ).scalars()

        return OrganizationVerificationRequestReviewReadModel(
            id=request.id,
            source_admin_unit_id=request.source_admin_unit_id,
            target_admin_unit_id=request.target_admin_unit_id,
            review_status=OrganizationVerificationRequestReviewStatus(
                request.review_status
            ),
            source_admin_unit=VerificationReviewOrganizationReadModel(
                id=source.id,
                name=source.name,
                short_name=source.short_name,
                url=source.url,
                email=source.email,
                phone=source.phone,
                fax=source.fax,
                description=source.description,
                is_verified=bool(is_verified),
                created_at=source.created_at,
                updated_at=source.updated_at,
                location=to_location_read_model(source.location),
                logo=to_image_read_model(source.logo),
                logo_id=source.logo_id,
                can_verify_other=bool(source.can_verify_other),
                incoming_reference_requests_allowed=bool(
                    source.incoming_reference_requests_allowed
                ),
                members=[to_organization_member_read_model(m) for m in members],
            ),
        )

    def _list(self, filters, query):
        filters = [
            *filters,
            *trackable_filters(AdminUnitVerificationRequest, query.trackable),
        ]
        stmt = (
            select(AdminUnitVerificationRequest)
            .where(*filters)
            .options(*_options)
            .order_by(
                *trackable_order(AdminUnitVerificationRequest, query.sort),
                AdminUnitVerificationRequest.created_at.desc(),
                AdminUnitVerificationRequest.id,
            )
        )
        count_stmt = select(AdminUnitVerificationRequest.id).where(*filters)
        return paginate(
            self.session, stmt, count_stmt, query.page, lambda row: _to_model(row[0])
        )


def _to_model(request) -> OrganizationVerificationRequestReadModel:
    return OrganizationVerificationRequestReadModel(
        id=request.id,
        source_admin_unit_id=request.source_admin_unit_id,
        target_admin_unit_id=request.target_admin_unit_id,
        review_status=OrganizationVerificationRequestReviewStatus(
            request.review_status
        ),
        rejection_reason=(
            OrganizationVerificationRequestRejectionReason(request.rejection_reason)
            if request.rejection_reason
            else None
        ),
        created_at=request.created_at,
        updated_at=request.updated_at,
        source_admin_unit=to_organization_ref_read_model(request.source_admin_unit),
        target_admin_unit=to_organization_ref_read_model(request.target_admin_unit),
    )
