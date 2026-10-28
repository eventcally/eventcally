from functools import wraps
from typing import Optional

from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from dependency_injector.wiring import Provide, inject
from flask import abort, current_app, g, request
from flask_apispec import marshal_with
from flask_apispec.annotations import annotate
from flask_apispec.views import MethodResource
from werkzeug.exceptions import UnsupportedMediaType

from project.application.message_bus import MessageBus
from project.application.queries import (
    GetApiKeyByHashQuery,
    GetCurrentOrganizationQuery,
    GetResourceOwnerQuery,
    ResourceKind,
)
from project.application.query_bus import QueryBus
from project.application.services.abstract_app_context_provider import (
    AbstractAppContextProvider,
)
from project.container import Application
from project.infrastructure.extensions import limiter
from project.presentation.api.schemas import (
    ErrorResponseSchema,
    TooManyRequestsResponseSchema,
    UnprocessableEntityResponseSchema,
)
from project.presentation.shared.oauth2_extensions import require_oauth
from project.presentation.shared.rate_limit import (
    api_rate_limit_scope,
    get_limit_decorator_for_provider,
)
from project.shared.utils import hash_api_key


def etag_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.add_etag()
        return response.make_conditional(request)

    return wrapper


def get_api_key_from_request() -> bool:
    request_api_key = request.headers.get("X-API-Key")
    if not request_api_key:
        return False

    api_key = current_app.container.cqrs.query_bus().handle(
        GetApiKeyByHashQuery(key_hash=hash_api_key(request_api_key))
    )
    return api_key if api_key else False


class AppTokenRequiredException(OAuth2Error):
    error = "app_token_required"
    description = "App token required."


def require_api_access(scopes=None, app_token_required=False):
    def inner_decorator(func):
        def wrapped(*args, **kwargs):  # see authlib ResourceProtector#__call__
            limit_decorator = None
            try:  # pragma: no cover
                try:
                    token = require_oauth.acquire_token(scopes)

                    if app_token_required and (
                        not token or not token.app_id
                    ):  # pragma: no cover
                        raise AppTokenRequiredException()
                    limit_decorator = get_limit_decorator_for_provider(token)
                except OAuth2Error as error:
                    require_oauth.raise_error_response(error)
            except Exception as e:
                if app_token_required:
                    raise e
                api_key = get_api_key_from_request()
                if api_key:
                    limit_decorator = get_limit_decorator_for_provider(api_key)
                else:
                    if current_app.config["API_READ_ANONYM"]:
                        limit_decorator = limiter.shared_limit(
                            "60/minute", scope=api_rate_limit_scope
                        )
                    else:
                        raise e

            with limit_decorator:
                return func(*args, **kwargs)

        scope_list = scopes if type(scopes) is list else [scopes] if scopes else list()
        security = [
            {
                "oauth2AuthCode": scope_list,
                "oauth2ClientCredentials": scope_list,
            }
        ]

        if not scope_list and not app_token_required:
            security.append(
                {
                    "apiKey": scope_list,
                }
            )

        annotate(
            wrapped,
            "docs",
            [{"security": security}],
        )
        return wrapped

    return inner_decorator


def organization_item_or_404(
    query_bus: QueryBus, kind: ResourceKind, organization_id: int, item_id: int
) -> None:
    """404 unless the item exists and belongs to the organization (of the side `kind`
    names). Other organizations' items are not revealed."""
    owner_id = query_bus.handle(GetResourceOwnerQuery(kind=kind, id=item_id))

    if owner_id is None or owner_id != organization_id:
        abort(404)


def require_organization_api_access(
    scope: str,
    resource: Optional[ResourceKind] = None,
    item_arg: Optional[str] = None,
    **outer_kwargs,
):
    """Gate an endpoint on an organization permission. Without `resource` the path id
    is the organization, with it the id of a resource owned by one.

    With `item_arg` (requires `resource`) the path id is the organization and the
    path argument `item_arg` the id of an item of the side `resource` names: after the
    access checks an item of another organization (or of the other side) answers 404.
    """

    def inner_decorator(func):
        @require_api_access([scope])
        @wraps(func)
        def wrapped(*args, **kwargs):
            from authlib.integrations.flask_oauth2 import current_token
            from flask import abort, g

            from project.presentation.shared.access import (
                access_or_401,
                login_api_user_or_401,
            )
            from project.presentation.shared.current_admin_unit import (
                set_current_admin_unit,
            )
            from project.presentation.shared.query_results import result_or_404
            from project.shared.context import ContextProvider

            query_bus = current_app.container.cqrs.query_bus()
            api_command_context = {}
            id = kwargs.get("id")

            if resource and not item_arg:
                admin_unit_id = result_or_404(
                    query_bus.handle(GetResourceOwnerQuery(kind=resource, id=id))
                )
                api_command_context["id"] = id
            else:
                admin_unit_id = id

            if current_token and current_token.app_installation:
                if (
                    current_token.app_installation.admin_unit_id != admin_unit_id
                ):  # pragma: no cover
                    abort(401)
            else:
                login_api_user_or_401()

            admin_unit = result_or_404(
                query_bus.handle(GetCurrentOrganizationQuery(id=admin_unit_id))
            )
            permission = scope.replace("organization.", "")
            access_or_401(admin_unit, permission)
            set_current_admin_unit(admin_unit)

            if item_arg:
                organization_item_or_404(query_bus, resource, id, kwargs[item_arg])
                api_command_context["id"] = kwargs[item_arg]

            api_command_context["admin_unit_id"] = admin_unit_id
            api_command_context["actor"] = ContextProvider().current_actor
            setattr(g, "api_command_context", api_command_context)

            return func(*args, **kwargs)

        return wrapped

    return inner_decorator


@marshal_with(ErrorResponseSchema, 400, "Bad Request")
@marshal_with(UnprocessableEntityResponseSchema, 422, "Unprocessable Entity")
@marshal_with(TooManyRequestsResponseSchema, 429, "Too many requests")
class BaseResource(MethodResource):
    decorators = [etag_cache]

    @inject
    def __init__(
        self,
        message_bus: MessageBus = Provide[Application.cqrs.message_bus],
        query_bus: QueryBus = Provide[Application.cqrs.query_bus],
        app_context_provider: AbstractAppContextProvider = Provide[
            Application.context.app_context_provider
        ],
    ):
        self.message_bus = message_bus
        self.query_bus = query_bus
        self.app_context_provider = app_context_provider

    def get_json_body(self) -> dict:
        """Parsed JSON body, treating a missing one as empty.

        Resources that build their command from a plain schema must not use
        `request.json` directly: it raises on a request without a body, while
        webargs' `use_kwargs` — which those resources replaced — parsed the
        same request as `{}`. Endpoints whose payload is entirely optional
        stay callable with no body that way. A malformed non-empty body still
        raises, so it keeps answering 400 rather than being read as empty.
        """
        if not request.get_data(cache=True):
            return {}

        try:
            return request.get_json() or {}
        except UnsupportedMediaType:
            return {}

    def load_command(self, schema_cls):
        """Build a command from the request body via a plain schema, so an
        invalid payload surfaces as a 422 instead of escaping as a 500."""
        return schema_cls(context=g.api_command_context).load(self.get_json_body())


def current_token_as_app_or_401():
    if not current_token or not current_token.app_id:  # pragma: no cover
        abort(401)
