from dependency_injector.wiring import Provide, inject
from flask import abort, url_for
from flask_security import current_user

from project.application.queries import (
    GetOrganizationQuery,
    GetOutgoingOrganizationRelationByTargetQuery,
    SearchOrganizationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.public import bff_public_bp
from project.presentation.bff.public.schemas import (
    PublicOrganization,
    PublicOrganizationListParams,
    PublicOrganizationPage,
    PublicOrganizationRef,
    PublicOrganizationRelation,
    PublicOrganizerLocation,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import can_verify_admin_unit, has_access
from project.presentation.shared.current_admin_unit import get_current_admin_unit
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.urls import url_for_image


@bff_route(
    bff_public_bp,
    "/organizations",
    query=PublicOrganizationListParams,
    response=PublicOrganizationPage,
    summary="List organizations",
)
@inject
def list_organizations(
    query: PublicOrganizationListParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    keyword = (query.keyword or "").strip() or None
    page = query_bus.handle(
        SearchOrganizationsQuery(
            keyword=keyword,
            include_unverified=can_verify_admin_unit(),
            page=query.to_page_request(),
        )
    )

    if page.is_out_of_range:
        abort(404)

    return PublicOrganizationPage.from_page(page)


def _relation_for(target, query_bus: QueryBus):
    """The relation card of the visitor's current organization to `target`, or `None`
    unless the visitor may maintain relations from an organization that can use them."""
    if not current_user.is_authenticated:
        return None

    source = get_current_admin_unit()
    if not source or source.id == target.id:
        return None

    if not has_access(source, "outgoing_organization_relations:write"):
        return None

    if not (source.can_verify_other or source.incoming_reference_requests_allowed):
        return None

    try:
        relation = query_bus.handle(
            GetOutgoingOrganizationRelationByTargetQuery(
                admin_unit_id=source.id, target_admin_unit_id=target.id
            )
        )
    except UnauthorizedError:  # pragma: no cover
        return None

    if relation:
        return PublicOrganizationRelation(
            source=PublicOrganizationRef(id=source.id, name=source.name),
            relation_id=relation.id,
            verify=relation.verify,
            auto_verify_event_reference_requests=relation.auto_verify_event_reference_requests,
            edit_url=url_for(
                "manage_admin_unit.outgoing_organization_relation_update",
                id=source.id,
                organization_relation_id=relation.id,
            ),
        )

    return PublicOrganizationRelation(
        source=PublicOrganizationRef(id=source.id, name=source.name),
        create_url=url_for(
            "manage_admin_unit.outgoing_organization_relation_create",
            id=source.id,
            target=target.id,
            verify=1,
        ),
    )


@bff_route(
    bff_public_bp,
    "/organizations/<int:id>",
    response=PublicOrganization,
    summary="Get organization",
)
@inject
def get_organization(id, query_bus: QueryBus = Provide[Application.cqrs.query_bus]):
    organization = result_or_404(query_bus.handle(GetOrganizationQuery(id=id)))

    location = None
    if organization.location and (
        organization.location.street
        or organization.location.postalCode
        or organization.location.city
    ):
        location = PublicOrganizerLocation(
            street=organization.location.street,
            postal_code=organization.location.postalCode,
            city=organization.location.city,
        )

    return PublicOrganization(
        id=organization.id,
        name=organization.name,
        short_name=organization.short_name,
        url=organization.url,
        email=organization.email,
        phone=organization.phone,
        fax=organization.fax,
        description=organization.description,
        is_verified=organization.is_verified,
        location=location,
        logo_url=url_for_image(organization.logo, s=120) if organization.logo else None,
        ical_url=url_for("main.organization_ical", id=organization.id, _external=True),
        relation=_relation_for(organization, query_bus),
    )
