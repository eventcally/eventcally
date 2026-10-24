from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    CreateOrganizationRelationCommand,
    UpdateOrganizationRelationCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetManageableOrganizationQuery,
    GetOrganizationQuery,
    GetOutgoingOrganizationRelationByTargetQuery,
    GetOutgoingOrganizationRelationQuery,
    PageRequest,
    SearchOrganizationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.types import unset
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.events import LOOKUP_PER_PAGE
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    ManageRef,
    ManageRefList,
    ManageRefParams,
    OrganizationRelationCreate,
    OrganizationRelationForm,
    OrganizationRelationFormParams,
    OrganizationRelationSaved,
    OrganizationRelationUpdate,
)
from project.presentation.bff.routing import bff_route
from project.presentation.shared.access import has_access
from project.presentation.shared.query_results import result_or_404


def _write_access_or_forbidden(id: int):
    if not has_access(SimpleNamespace(id=id), "outgoing_organization_relations:write"):
        raise UnauthorizedError()


def _organization(id: int, query_bus: QueryBus):
    _write_access_or_forbidden(id)
    return result_or_404(query_bus.handle(GetManageableOrganizationQuery(id=id)))


def _relation_or_404(id: int, relation_id: int, query_bus: QueryBus):
    _write_access_or_forbidden(id)

    # Do not reveal the relations of other organizations: the query refuses them
    # for lack of permission on their source organization.
    try:
        relation = result_or_404(
            query_bus.handle(GetOutgoingOrganizationRelationQuery(id=relation_id))
        )
    except UnauthorizedError:
        abort(404)

    if relation.source_admin_unit_id != id:  # pragma: no cover
        abort(404)

    return relation


def _list_url(id: int) -> str:
    return url_for("manage_admin_unit.outgoing_organization_relations", id=id)


def _saved(id: int, relation_id: int, text: str) -> OrganizationRelationSaved:
    flash(text, "success")
    return OrganizationRelationSaved(id=relation_id, redirect_url=_list_url(id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-organization-relations/create-form",
    query=OrganizationRelationFormParams,
    response=OrganizationRelationForm,
    summary="Get the form to create an outgoing organization relation",
)
@inject
def get_outgoing_organization_relation_create_form(
    id: int,
    query: OrganizationRelationFormParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, query_bus)
    target = None

    if query.target:
        # An unknown organization is ignored, the field stays empty.
        found = query_bus.handle(GetOrganizationQuery(id=query.target))
        target = ManageRef(id=found.id, name=found.name) if found else None

    return OrganizationRelationForm(
        target=target,
        verify=organization.can_verify_other and query.verify == 1,
        can_verify_other=organization.can_verify_other,
        list_url=_list_url(id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-organization-relations/organizations",
    query=ManageRefParams,
    response=ManageRefList,
    summary="Look up the organizations to relate to",
)
@inject
def lookup_relation_organizations(
    id: int,
    query: ManageRefParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, query_bus)
    page = query_bus.handle(
        SearchOrganizationsQuery(
            keyword=query.keyword,
            include_unverified=organization.can_verify_other,
            page=PageRequest(page=1, per_page=LOOKUP_PER_PAGE),
        )
    )
    return ManageRefList(items=[ManageRef(id=o.id, name=o.name) for o in page.items])


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-organization-relations/<int:relation_id>",
    response=OrganizationRelationForm,
    summary="Get the form to update an outgoing organization relation",
)
@inject
def get_outgoing_organization_relation_form(
    id: int,
    relation_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, query_bus)
    relation = _relation_or_404(id, relation_id, query_bus)
    target = relation.target_admin_unit

    return OrganizationRelationForm(
        id=relation.id,
        target=ManageRef(id=target.id, name=target.name),
        verify=relation.verify,
        auto_verify_event_reference_requests=relation.auto_verify_event_reference_requests,
        can_verify_other=organization.can_verify_other,
        list_url=_list_url(id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-organization-relations",
    method="POST",
    body=OrganizationRelationCreate,
    response=OrganizationRelationSaved,
    status=201,
    summary="Create an outgoing organization relation",
)
@inject
def create_outgoing_organization_relation(
    id: int,
    body: OrganizationRelationCreate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, query_bus)

    if body.target_admin_unit_id is None:
        raise FieldValidationError(
            ["target_admin_unit_id"], gettext("This field is required.")
        )

    if query_bus.handle(
        GetOutgoingOrganizationRelationByTargetQuery(
            admin_unit_id=id, target_admin_unit_id=body.target_admin_unit_id
        )
    ):
        raise FieldValidationError(
            ["target_admin_unit_id"],
            gettext("A relation to this organization already exists."),
        )

    result = message_bus.handle_command(
        CreateOrganizationRelationCommand(
            actor=actor(),
            source_admin_unit_id=id,
            target_admin_unit_id=body.target_admin_unit_id,
            auto_verify_event_reference_requests=body.auto_verify_event_reference_requests,
            verify=body.verify if organization.can_verify_other else False,
        )
    )

    return _saved(
        id,
        result.id,
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=gettext("Outgoing organization relation"),
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/outgoing-organization-relations/<int:relation_id>",
    method="PUT",
    body=OrganizationRelationUpdate,
    response=OrganizationRelationSaved,
    summary="Update an outgoing organization relation",
)
@inject
def update_outgoing_organization_relation(
    id: int,
    relation_id: int,
    body: OrganizationRelationUpdate,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    organization = _organization(id, query_bus)
    _relation_or_404(id, relation_id, query_bus)

    message_bus.handle_command(
        UpdateOrganizationRelationCommand(
            actor=actor(),
            id=relation_id,
            auto_verify_event_reference_requests=body.auto_verify_event_reference_requests,
            verify=body.verify if organization.can_verify_other else unset,
        )
    )

    return _saved(
        id,
        relation_id,
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=gettext("Outgoing organization relation"),
        ),
    )
