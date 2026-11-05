from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, flash, url_for
from flask_babel import gettext
from markupsafe import Markup, escape

from project.application.commands import (
    InstallAppCommand,
    UninstallAppCommand,
    UpdateAppInstallationPermissionsCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetAppInstallationQuery,
    GetInstallableAppQuery,
    ListAppInstallationsQuery,
)
from project.application.query_bus import QueryBus
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    AppInstallationListItem,
    AppInstallationListPage,
    AppInstallationRead,
    AppInstallationSaved,
    AppInstallSave,
    InstallableAppRead,
    ManageAudit,
    ManageDeleted,
    ManageDeleteSave,
    ManageMessage,
)
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.access import has_access
from project.presentation.shared.permissions import get_organization_permission_infos
from project.presentation.shared.query_results import result_or_404


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _model_name() -> str:
    return gettext("App installation")


def _read_url(id: int, installation_id: int) -> str:
    return url_for(
        "manage_admin_unit.app_installation", id=id, app_installation_id=installation_id
    )


def _labels(permissions: list[str]) -> list[str]:
    return [str(i.label) for i in get_organization_permission_infos(permissions)]


def _installation_or_404(
    id: int, installation_id: int, permission: str, query_bus: QueryBus
):
    _access_or_forbidden(id, permission)

    try:
        installation = result_or_404(
            query_bus.handle(GetAppInstallationQuery(id=installation_id))
        )
    except UnauthorizedError:
        abort(404)

    if installation.admin_unit_id != id:
        abort(404)

    return installation


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/app-installations",
    query=PageParams,
    response=AppInstallationListPage,
    summary="List the apps installed by the organization",
)
@inject
def list_organization_app_installations(
    id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "app_installations:read")
    page = result_or_404(
        query_bus.handle(
            ListAppInstallationsQuery(admin_unit_id=id, page=query.to_page_request())
        )
    )

    if page.is_out_of_range:
        abort(404)

    return AppInstallationListPage(
        items=[
            AppInstallationListItem(
                id=i.id, app=i.oauth2_client.client_name, created_at=i.created_at
            )
            for i in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=has_access(SimpleNamespace(id=id), "app_installations:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/app-installations/<int:installation_id>",
    response=AppInstallationRead,
    summary="Get an app installation of the organization",
)
@inject
def get_organization_app_installation(
    id: int,
    installation_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    installation = _installation_or_404(
        id, installation_id, "app_installations:read", query_bus
    )
    requested = installation.oauth2_client.app_permissions

    return AppInstallationRead(
        id=installation.id,
        app=installation.oauth2_client.client_name,
        permissions=_labels(installation.permissions),
        requested_permissions=_labels(requested),
        needs_permission_update=set(requested) != set(installation.permissions),
        created_at=installation.created_at,
        audit=(
            ManageAudit(**installation.audit.model_dump())
            if installation.audit
            else None
        ),
        can_write=has_access(SimpleNamespace(id=id), "app_installations:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/app-installations/<int:installation_id>/permissions",
    method="PUT",
    response=ManageMessage,
    summary="Accept the permissions the app requests now",
)
@inject
def accept_organization_app_installation_permissions(
    id: int,
    installation_id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    installation = _installation_or_404(
        id, installation_id, "app_installations:write", query_bus
    )
    message_bus.handle_command(
        UpdateAppInstallationPermissionsCommand(
            actor=actor(),
            id=installation_id,
            permissions=set(installation.oauth2_client.app_permissions),
        )
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        )
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/app-installations/<int:installation_id>/delete",
    method="POST",
    body=ManageDeleteSave,
    response=ManageDeleted,
    summary="Uninstall an app of the organization",
)
@inject
def delete_organization_app_installation(
    id: int,
    installation_id: int,
    body: ManageDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _installation_or_404(id, installation_id, "app_installations:write", query_bus)
    message_bus.handle_command(UninstallAppCommand(actor=actor(), id=installation_id))
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=_model_name(),
    )

    if not body.inline:
        flash(message, "success")

    return ManageDeleted(
        message=message,
        redirect_url=url_for("manage_admin_unit.app_installations", id=id),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/installable-apps/<int:app_id>",
    response=InstallableAppRead,
    summary="Get what an organization sees of an app before installing it",
)
@inject
def get_installable_app(
    id: int,
    app_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "app_installations:write")
    app = result_or_404(query_bus.handle(GetInstallableAppQuery(id=app_id)))

    return InstallableAppRead(
        id=app.id,
        client_name=app.client_name,
        homepage_url=app.homepage_url,
        description=app.description,
        permissions=_labels(app.app_permissions),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/app-installations",
    method="POST",
    body=AppInstallSave,
    response=AppInstallationSaved,
    status=201,
    summary="Install an app for the organization",
)
@inject
def install_organization_app(
    id: int,
    body: AppInstallSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "app_installations:write")
    app = result_or_404(query_bus.handle(GetInstallableAppQuery(id=body.app_id)))
    result = message_bus.handle_command(
        InstallAppCommand(actor=actor(), admin_unit_id=id, app_id=app.id)
    )
    text = gettext("App successfully installed")

    if app.setup_url:
        # The message plus a " – Setup" link, like `flash_message` of the web views.
        link = Markup(' &ndash; <a href="%s">%s</a>') % (
            app.setup_url,
            gettext("Setup"),
        )
        flash(escape(text) + link, "success")
    else:
        flash(text, "success")

    return AppInstallationSaved(id=result.id, redirect_url=_read_url(id, result.id))
