from types import SimpleNamespace

from dependency_injector.wiring import Provide, inject
from flask import abort, after_this_request, flash, url_for
from flask_babel import gettext

from project.application.commands import (
    AttemptToDeliverWebhookCommand,
    CreateAppCommand,
    CreateAppKeyCommand,
    DeleteAppCommand,
    DeleteAppKeyCommand,
    UpdateAppCommand,
)
from project.application.message_bus import MessageBus
from project.application.queries import (
    GetAppKeyQuery,
    GetAppQuery,
    GetAppWebhookDeliveryQuery,
    ListAppKeysQuery,
    ListAppsQuery,
    ListAppWebhookDeliveriesQuery,
    ListAppWebhookDeliveryAttemptsQuery,
)
from project.application.queries.page_request import MAX_PER_PAGE, PageRequest
from project.application.query_bus import QueryBus
from project.application.webhooks.app_installation_webhooks import (
    app_installation_webhook_infos,
)
from project.application.webhooks.app_webhooks import app_webhook_infos
from project.container import Application
from project.domain.errors.unauthorized_error import UnauthorizedError
from project.domain.models.value_objects.webhook_value_object import WebhookValueObject
from project.presentation.bff.errors import FieldValidationError
from project.presentation.bff.manage import bff_manage_bp
from project.presentation.bff.manage.organization_form import actor
from project.presentation.bff.manage.schemas import (
    AppFormOptions,
    AppKeyCreated,
    AppKeyItem,
    AppListItem,
    AppListPage,
    AppPermissionChoice,
    AppRead,
    AppSave,
    AppSaved,
    AppWebhookFields,
    ManageAudit,
    ManageDeleted,
    ManageMessage,
    ManageNameDeleteSave,
    WebhookDeliveryAttemptItem,
    WebhookDeliveryAttemptListPage,
    WebhookDeliveryItem,
    WebhookDeliveryListPage,
    WebhookDeliveryRead,
)
from project.presentation.bff.routing import bff_route
from project.presentation.bff.schemas import PageParams
from project.presentation.shared.access import has_access
from project.presentation.shared.permissions import (
    get_organization_permission_infos,
    organization_app_permission_infos,
)
from project.presentation.shared.query_results import result_or_404
from project.presentation.shared.scopes import scopes as available_scopes
from project.shared.utils import strings_are_equal_ignoring_case

_EVENT_TYPES = [
    i.event_type for i in app_webhook_infos + app_installation_webhook_infos
]


def _access_or_forbidden(id: int, permission: str):
    if not has_access(SimpleNamespace(id=id), permission):
        raise UnauthorizedError()


def _can(id: int, permission: str) -> bool:
    return has_access(SimpleNamespace(id=id), permission)


def _model_name() -> str:
    return gettext("App")


def _read_url(id: int, app_id: int) -> str:
    return url_for("manage_admin_unit.app", id=id, app_id=app_id)


def _app_or_404(id: int, app_id: int, permission: str, query_bus: QueryBus):
    _access_or_forbidden(id, permission)

    # Do not reveal the apps of other organizations: the query refuses them for lack of
    # permission.
    try:
        app = result_or_404(query_bus.handle(GetAppQuery(id=app_id)))
    except UnauthorizedError:
        abort(404)

    if app.admin_unit_id != id:
        abort(404)

    return app


def _app_title(app) -> str:
    return app.client_name or f"{gettext('OAuth2 client')} {app.id}"


def _scope_of(body: AppSave) -> str:
    unknown = [scope for scope in body.scopes if scope not in available_scopes]

    if unknown:
        raise FieldValidationError(
            ["scopes"], gettext("'%(value)s' is not a valid choice", value=unknown[0])
        )

    return " ".join(body.scopes)


def _permissions_of(body: AppSave) -> set[str]:
    valid = {i.permission for i in organization_app_permission_infos}
    unknown = [p for p in body.app_permissions if p not in valid]

    if unknown:
        raise FieldValidationError(
            ["app_permissions"],
            gettext("'%(value)s' is not a valid choice", value=unknown[0]),
        )

    return set(body.app_permissions)


def _webhook_of(body: AppSave):
    webhook = body.webhook
    unknown = [t for t in webhook.event_types if t not in _EVENT_TYPES]

    if unknown:
        raise FieldValidationError(
            ["webhook", "event_types"],
            gettext("'%(value)s' is not a valid choice", value=unknown[0]),
        )

    if not webhook.url:
        return None

    return WebhookValueObject(
        url=webhook.url,
        secret=webhook.secret or None,
        disabled=webhook.disabled,
        event_types=set(webhook.event_types),
    )


def _redirect_uris_of(body: AppSave) -> set[str]:
    return {uri.strip() for uri in body.redirect_uris if uri.strip()}


def _permission_labels(permissions: list[str]) -> list[str]:
    return [str(i.label) for i in get_organization_permission_infos(permissions)]


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps",
    query=PageParams,
    response=AppListPage,
    summary="List the apps of the organization",
)
@inject
def list_organization_apps(
    id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _access_or_forbidden(id, "apps:read")
    page = result_or_404(
        query_bus.handle(ListAppsQuery(admin_unit_id=id, page=query.to_page_request()))
    )

    if page.is_out_of_range:
        abort(404)

    return AppListPage(
        items=[AppListItem(id=a.id, client_name=a.client_name) for a in page.items],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=_can(id, "apps:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/form",
    response=AppFormOptions,
    summary="Get the choices of the app form",
)
def get_organization_app_form(id: int):
    _access_or_forbidden(id, "apps:write")
    return AppFormOptions(
        scopes=list(available_scopes),
        app_permissions=[
            AppPermissionChoice(permission=i.permission, label=str(i.label))
            for i in organization_app_permission_infos
        ],
        event_types=_EVENT_TYPES,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps",
    method="POST",
    body=AppSave,
    response=AppSaved,
    status=201,
    summary="Create an app of the organization",
)
@inject
def create_organization_app(
    id: int,
    body: AppSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
):
    _access_or_forbidden(id, "apps:write")
    result = message_bus.handle_command(
        CreateAppCommand(
            actor=actor(),
            admin_unit_id=id,
            name=body.client_name,
            app_permissions=_permissions_of(body),
            redirect_uris=_redirect_uris_of(body),
            scope=_scope_of(body),
            description=body.description or None,
            homepage_url=body.homepage_url or None,
            setup_url=body.setup_url or None,
            webhook=_webhook_of(body),
        )
    )
    flash(
        gettext(
            "%(model_display_name)s successfully created",
            model_display_name=_model_name(),
        ),
        "success",
    )

    return AppSaved(id=result.id, redirect_url=_read_url(id, result.id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>",
    response=AppRead,
    summary="Get an app of the organization with its keys",
)
@inject
def get_organization_app(
    id: int,
    app_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    app = _app_or_404(id, app_id, "apps:read", query_bus)
    can_read_keys = _can(id, "app_keys:read")
    keys = []

    if can_read_keys:
        page = query_bus.handle(
            ListAppKeysQuery(app_id=app_id, page=PageRequest(per_page=MAX_PER_PAGE))
        )
        keys = [AppKeyItem(id=k.id, kid=k.kid, checksum=k.checksum) for k in page.items]

    return AppRead(
        id=app.id,
        client_id=app.client_id,
        client_secret=app.client_secret,
        client_name=app.client_name,
        client_uri=app.client_uri,
        scope=app.scope,
        scopes=[scope for scope in app.scope.split(" ") if scope],
        redirect_uris=app.redirect_uris,
        grant_types=app.grant_types,
        response_types=app.response_types,
        token_endpoint_auth_method=app.token_endpoint_auth_method,
        app_permissions=_permission_labels(app.app_permissions),
        homepage_url=app.homepage_url,
        setup_url=app.setup_url,
        webhook_url=app.webhook.url if app.webhook else None,
        description=app.description,
        keys=keys,
        can_read_keys=can_read_keys,
        can_write_keys=_can(id, "app_keys:write"),
        can_read_deliveries=_can(id, "webhook_deliveries:read"),
        audit=ManageAudit(**app.audit.model_dump()) if app.audit else None,
        can_write=_can(id, "apps:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/form",
    response=AppSave,
    summary="Get the values of the app form",
)
@inject
def get_organization_app_values(
    id: int,
    app_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    app = _app_or_404(id, app_id, "apps:write", query_bus)
    webhook = app.webhook

    return AppSave(
        client_name=app.client_name or "",
        redirect_uris=app.redirect_uris,
        scopes=[scope for scope in app.scope.split(" ") if scope],
        app_permissions=app.app_permissions,
        homepage_url=app.homepage_url,
        setup_url=app.setup_url,
        description=app.description,
        webhook=(
            AppWebhookFields(
                url=webhook.url,
                secret=webhook.secret,
                disabled=webhook.disabled,
                event_types=webhook.event_types,
            )
            if webhook
            else AppWebhookFields()
        ),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>",
    method="PUT",
    body=AppSave,
    response=AppSaved,
    summary="Update an app of the organization",
)
@inject
def update_organization_app(
    id: int,
    app_id: int,
    body: AppSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _app_or_404(id, app_id, "apps:write", query_bus)
    message_bus.handle_command(
        UpdateAppCommand(
            actor=actor(),
            id=app_id,
            name=body.client_name,
            app_permissions=_permissions_of(body),
            redirect_uris=_redirect_uris_of(body),
            scope=_scope_of(body),
            description=body.description or None,
            homepage_url=body.homepage_url or None,
            setup_url=body.setup_url or None,
            webhook=_webhook_of(body),
        )
    )
    flash(
        gettext(
            "%(model_display_name)s successfully updated",
            model_display_name=_model_name(),
        ),
        "success",
    )

    return AppSaved(id=app_id, redirect_url=_read_url(id, app_id))


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/delete",
    method="POST",
    body=ManageNameDeleteSave,
    response=ManageDeleted,
    summary="Delete an app of the organization after typing its name",
)
@inject
def delete_organization_app(
    id: int,
    app_id: int,
    body: ManageNameDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    app = _app_or_404(id, app_id, "apps:write", query_bus)

    if not strings_are_equal_ignoring_case(body.name, app.client_name or ""):
        raise FieldValidationError(
            ["name"], gettext("Entered name does not match app client name")
        )

    message_bus.handle_command(DeleteAppCommand(actor=actor(), id=app_id))
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=_model_name(),
    )

    if not body.inline:
        flash(message, "success")

    return ManageDeleted(
        message=message, redirect_url=url_for("manage_admin_unit.apps", id=id)
    )


# Keys


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/keys",
    method="POST",
    response=AppKeyCreated,
    status=201,
    summary="Create a key of the app; the private key is only part of this answer",
)
@inject
def create_organization_app_key(
    id: int,
    app_id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _app_or_404(id, app_id, "app_keys:write", query_bus)

    @after_this_request
    def no_store(response):
        response.headers["Cache-Control"] = "no-store"
        return response

    result = message_bus.handle_command(
        CreateAppKeyCommand(actor=actor(), admin_unit_id=id, app_id=app_id)
    )
    key = query_bus.handle(GetAppKeyQuery(id=result.id))

    return AppKeyCreated(id=result.id, kid=key.kid, private_pem=result.private_pem)


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/keys/<int:key_id>/delete",
    method="POST",
    body=ManageNameDeleteSave,
    response=ManageDeleted,
    summary="Delete a key of the app after typing its KID",
)
@inject
def delete_organization_app_key(
    id: int,
    app_id: int,
    key_id: int,
    body: ManageNameDeleteSave,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _app_or_404(id, app_id, "app_keys:write", query_bus)
    key = result_or_404(query_bus.handle(GetAppKeyQuery(id=key_id)))

    if key.oauth2_client_id != app_id:
        abort(404)

    if not strings_are_equal_ignoring_case(body.name, key.kid):
        raise FieldValidationError(
            ["name"],
            gettext(
                "Entered %(property_name)s does not match %(model_display_name)s %(property_name)s",
                model_display_name=gettext("App key"),
                property_name=gettext("KID"),
            ),
        )

    message_bus.handle_command(DeleteAppKeyCommand(actor=actor(), id=key_id))
    message = gettext(
        "%(model_display_name)s successfully deleted",
        model_display_name=gettext("App key"),
    )

    if not body.inline:
        flash(message, "success")

    return ManageDeleted(message=message, redirect_url=_read_url(id, app_id))


# Webhook deliveries and their attempts


def _delivery_or_404(
    id: int, app_id: int, delivery_id: int, permission: str, query_bus: QueryBus
):
    app = _app_or_404(id, app_id, permission, query_bus)
    # The app belongs to the organization and the permission was checked above.
    delivery = result_or_404(
        query_bus.handle(GetAppWebhookDeliveryQuery(id=delivery_id))
    )

    if delivery.app_id != app_id or delivery.admin_unit_id != id:
        abort(404)

    return app, delivery


def _delivery_item(delivery) -> dict:
    installation = delivery.app_installation
    return dict(
        id=delivery.id,
        event_type=delivery.webhook_event.event_type,
        timestamp=delivery.webhook_event.timestamp,
        organization=installation.admin_unit.name if installation else None,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/webhook-deliveries",
    query=PageParams,
    response=WebhookDeliveryListPage,
    summary="List the webhook deliveries of the app",
)
@inject
def list_organization_app_webhook_deliveries(
    id: int,
    app_id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    app = _app_or_404(id, app_id, "webhook_deliveries:read", query_bus)
    page = result_or_404(
        query_bus.handle(
            ListAppWebhookDeliveriesQuery(app_id=app_id, page=query.to_page_request())
        )
    )

    if page.is_out_of_range:
        abort(404)

    return WebhookDeliveryListPage(
        items=[WebhookDeliveryItem(**_delivery_item(d)) for d in page.items],
        app_title=_app_title(app),
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=False,
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/webhook-deliveries/<int:delivery_id>",
    response=WebhookDeliveryRead,
    summary="Get a webhook delivery of the app",
)
@inject
def get_organization_app_webhook_delivery(
    id: int,
    app_id: int,
    delivery_id: int,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    app, delivery = _delivery_or_404(
        id, app_id, delivery_id, "webhook_deliveries:read", query_bus
    )

    return WebhookDeliveryRead(
        **_delivery_item(delivery),
        app_id=app_id,
        app_title=_app_title(app),
        can_attempt=_can(id, "webhook_delivery_attempts:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/webhook-deliveries/<int:delivery_id>/attempts",
    query=PageParams,
    response=WebhookDeliveryAttemptListPage,
    summary="List the attempts to deliver a webhook",
)
@inject
def list_organization_app_webhook_delivery_attempts(
    id: int,
    app_id: int,
    delivery_id: int,
    query: PageParams,
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _delivery_or_404(
        id, app_id, delivery_id, "webhook_delivery_attempts:read", query_bus
    )
    page = result_or_404(
        query_bus.handle(
            ListAppWebhookDeliveryAttemptsQuery(
                webhook_delivery_id=delivery_id, page=query.to_page_request()
            )
        )
    )

    if page.is_out_of_range:
        abort(404)

    return WebhookDeliveryAttemptListPage(
        items=[
            WebhookDeliveryAttemptItem(
                id=a.id,
                start_at=a.start_at,
                end_at=a.end_at,
                url=a.url,
                status=a.status,
                status_code=a.status_code,
            )
            for a in page.items
        ],
        page=page.page,
        per_page=page.per_page,
        total=page.total,
        pages=page.pages,
        can_write=_can(id, "webhook_delivery_attempts:write"),
    )


@bff_route(
    bff_manage_bp,
    "/organizations/<int:id>/apps/<int:app_id>/webhook-deliveries/<int:delivery_id>/attempts",
    method="POST",
    response=ManageMessage,
    summary="Deliver a webhook again",
)
@inject
def create_organization_app_webhook_delivery_attempt(
    id: int,
    app_id: int,
    delivery_id: int,
    message_bus: MessageBus = Provide[Application.cqrs.message_bus],
    query_bus: QueryBus = Provide[Application.cqrs.query_bus],
):
    _delivery_or_404(
        id, app_id, delivery_id, "webhook_delivery_attempts:write", query_bus
    )
    message_bus.dispatch_command(
        AttemptToDeliverWebhookCommand(actor=actor(), webhook_delivery_id=delivery_id)
    )

    return ManageMessage(
        message=gettext(
            "%(model_display_name)s successfully created",
            model_display_name=gettext("Webhook delivery attempt"),
        )
    )
