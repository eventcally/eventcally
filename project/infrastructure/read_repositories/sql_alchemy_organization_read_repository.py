from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import joinedload, undefer, undefer_group

from project.application.queries.list_verifier_organizations_query import (
    ListVerifierOrganizationsQuery,
)
from project.application.queries.search_organizations_query import (
    SearchOrganizationsQuery,
)
from project.application.read_models.event_read_models import (
    VerifierOrganizationReadModel,
)
from project.application.read_models.organization_read_models import (
    OrganizationDetailReadModel,
    OrganizationListItemReadModel,
    OrganizationWidgetSettingsReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_organization_read_repository import (
    AbstractOrganizationReadRepository,
)
from project.domain.types.object_id import ObjectId
from project.infrastructure.read_repositories.event_read_model_mappers import (
    to_organization_embed,
)
from project.infrastructure.read_repositories.query_helpers import (
    paginate,
    trackable_filters,
    trackable_order,
)
from project.infrastructure.read_repositories.read_model_mappers import (
    to_image_read_model,
    to_location_read_model,
)
from project.models import AdminUnit, Image, Location


class SqlAlchemyOrganizationReadRepository(AbstractOrganizationReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def search(
        self, query: SearchOrganizationsQuery
    ) -> Page[OrganizationListItemReadModel]:
        filters = [*trackable_filters(AdminUnit, query.trackable)]

        if not query.include_unverified:
            filters.append(AdminUnit.is_verified)

        if query.only_verifier:
            filters.append(
                and_(
                    AdminUnit.can_verify_other,
                    AdminUnit.incoming_verification_requests_allowed,
                )
            )

        if query.reference_request_for_admin_unit_id:
            filters.append(
                and_(
                    AdminUnit.id != query.reference_request_for_admin_unit_id,
                    AdminUnit.incoming_reference_requests_allowed,
                )
            )

        if query.incoming_verification_requests_postal_code:
            filters.append(
                or_(
                    AdminUnit.incoming_verification_requests_postal_codes.contains(
                        [query.incoming_verification_requests_postal_code]
                    ),
                    AdminUnit.incoming_verification_requests_postal_codes == "{}",
                )
            )

        if query.postal_codes:
            filters.append(
                or_(
                    *[
                        Location.postalCode.ilike(postal_code + "%")
                        for postal_code in query.postal_codes
                    ]
                )
            )

        order_by = [*trackable_order(AdminUnit, query.sort)]

        if query.keyword:
            like_keyword = "%" + query.keyword + "%"
            prefix = query.keyword + "%"
            filters.append(
                or_(
                    AdminUnit.name.ilike(like_keyword),
                    AdminUnit.short_name.ilike(like_keyword),
                )
            )
            order_by.extend(
                [
                    AdminUnit.name.ilike(prefix).desc(),
                    AdminUnit.short_name.ilike(prefix).desc(),
                ]
            )

        order_by.extend([func.lower(AdminUnit.name), AdminUnit.id])

        stmt = (
            select(AdminUnit, AdminUnit.is_verified)
            .join(AdminUnit.location, isouter=True)
            .where(*filters)
            .options(undefer_group("trackable"))
            .order_by(*order_by)
        )
        count_stmt = (
            select(AdminUnit.id).join(AdminUnit.location, isouter=True).where(*filters)
        )
        return paginate(self.session, stmt, count_stmt, query.page, _to_list_item)

    def list_verifiers(
        self, query: ListVerifierOrganizationsQuery
    ) -> Page[VerifierOrganizationReadModel]:
        page = self.search(
            SearchOrganizationsQuery(
                only_verifier=True,
                incoming_verification_requests_postal_code=query.postal_code,
                page=query.page,
            )
        )
        ids = [item.id for item in page.items]
        admin_units = {
            admin_unit.id: admin_unit
            for admin_unit in self.session.execute(
                select(AdminUnit)
                .where(AdminUnit.id.in_(ids))
                .options(
                    undefer(AdminUnit.logo_id),
                    undefer_group("detail"),
                    undefer_group("trackable"),
                    undefer(AdminUnit.incoming_verification_requests_text),
                    joinedload(AdminUnit.location),
                    joinedload(AdminUnit.logo).options(
                        undefer(Image.created_at),
                        undefer(Image.updated_at),
                        joinedload(Image.license),
                    ),
                )
            )
            .scalars()
            .all()
        }

        return Page[VerifierOrganizationReadModel](
            items=[
                VerifierOrganizationReadModel(
                    **to_organization_embed(
                        admin_units[item.id], item.is_verified
                    ).model_dump(),
                    incoming_verification_requests_text=(
                        admin_units[item.id].incoming_verification_requests_text
                    ),
                )
                for item in page.items
            ],
            page=page.page,
            per_page=page.per_page,
            total=page.total,
        )

    def get(self, object_id: ObjectId) -> Optional[OrganizationDetailReadModel]:
        row = self.session.execute(
            select(AdminUnit, AdminUnit.is_verified)
            .where(AdminUnit.id == object_id)
            .options(
                undefer_group("trackable"),
                undefer_group("detail"),
                joinedload(AdminUnit.location),
                joinedload(AdminUnit.logo).options(
                    undefer(Image.created_at),
                    undefer(Image.updated_at),
                    joinedload(Image.license),
                ),
            )
        ).one_or_none()

        if row is None:
            return None

        admin_unit, is_verified = row

        return OrganizationDetailReadModel(
            id=admin_unit.id,
            name=admin_unit.name,
            short_name=admin_unit.short_name,
            url=admin_unit.url,
            email=admin_unit.email,
            phone=admin_unit.phone,
            fax=admin_unit.fax,
            description=admin_unit.description,
            is_verified=bool(is_verified),
            created_at=admin_unit.created_at,
            updated_at=admin_unit.updated_at,
            location=to_location_read_model(admin_unit.location),
            logo=to_image_read_model(admin_unit.logo),
            can_verify_other=bool(admin_unit.can_verify_other),
            incoming_reference_requests_allowed=bool(
                admin_unit.incoming_reference_requests_allowed
            ),
        )

    def get_widget_settings(
        self, object_id: ObjectId
    ) -> Optional[OrganizationWidgetSettingsReadModel]:
        admin_unit = self.session.execute(
            select(AdminUnit)
            .where(AdminUnit.id == object_id)
            .options(undefer_group("widget"))
        ).scalar_one_or_none()

        if admin_unit is None:
            return None

        def hex_or_none(color):
            return color.hex if color else None

        return OrganizationWidgetSettingsReadModel(
            id=admin_unit.id,
            widget_font=admin_unit.widget_font,
            widget_background_color=hex_or_none(admin_unit.widget_background_color),
            widget_primary_color=hex_or_none(admin_unit.widget_primary_color),
            widget_link_color=hex_or_none(admin_unit.widget_link_color),
        )


def _to_list_item(row) -> OrganizationListItemReadModel:
    admin_unit, is_verified = row

    return OrganizationListItemReadModel(
        id=admin_unit.id,
        name=admin_unit.name,
        short_name=admin_unit.short_name,
        is_verified=bool(is_verified),
        created_at=admin_unit.created_at,
        updated_at=admin_unit.updated_at,
    )
