from functools import wraps

from authlib.integrations.flask_oauth2 import current_token
from authlib.oauth2 import OAuth2Error
from flask import abort, request
from flask_apispec import marshal_with
from flask_apispec.annotations import annotate
from flask_apispec.views import MethodResource
from flask_limiter.extension import LimitDecorator
from flask_wtf.csrf import validate_csrf

from project import app, csrf, db, limiter
from project.api.schemas import (
    ErrorResponseSchema,
    TooManyRequestsResponseSchema,
    UnprocessableEntityResponseSchema,
)
from project.models.api_key import ApiKey
from project.models.mixins.rate_limit_provider_mixin import RateLimitProviderMixin
from project.oauth2 import require_oauth
from project.utils import getattr_keypath, hash_api_key

api_rate_limit_scope = "api"


def get_limit_decorator_for_provider(
    provider: RateLimitProviderMixin,
) -> LimitDecorator:
    key = provider.get_rate_limit_key()
    return limiter.shared_limit(
        provider.get_rate_limit_value(),
        scope=api_rate_limit_scope,
        key_func=lambda: key,
    )


def etag_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.add_etag()
        return response.make_conditional(request)

    return wrapper


def is_internal_request() -> bool:
    try:
        validate_csrf(csrf._get_csrf_token())
        return True
    except Exception:
        return False


def get_api_key_from_request() -> bool:
    request_api_key = request.headers.get("X-API-Key")
    if not request_api_key:
        return False

    key_hash = hash_api_key(request_api_key)
    api_key = db.session.query(ApiKey).filter_by(key_hash=key_hash).first()
    if not api_key:
        return False

    return api_key


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
                if is_internal_request():
                    limit_decorator = limiter.shared_limit(
                        "1000/minute", scope=api_rate_limit_scope
                    )
                else:
                    api_key = get_api_key_from_request()
                    if api_key:
                        limit_decorator = get_limit_decorator_for_provider(api_key)
                    else:
                        if app.config["API_READ_ANONYM"]:
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


def require_organization_api_access(scope: str, model=None, **outer_kwargs):
    def inner_decorator(func):
        @require_api_access([scope])
        @wraps(func)
        def wrapped(*args, **kwargs):
            from authlib.integrations.flask_oauth2 import current_token
            from flask import abort, g

            from project.access import access_or_401, login_api_user_or_401
            from project.models import AdminUnit
            from project.views.utils import set_current_admin_unit

            id = kwargs.get("id")

            if model:
                instance = model.query.get_or_404(id)
                admin_unit_id_path = outer_kwargs.get(
                    "admin_unit_id_path", "admin_unit_id"
                )
                admin_unit_id = getattr_keypath(instance, admin_unit_id_path)
                setattr(g, "manage_admin_unit_instance", instance)
            else:
                admin_unit_id = id

            if current_token and current_token.app_installation:
                if (
                    current_token.app_installation.admin_unit_id != admin_unit_id
                ):  # pragma: no cover
                    abort(401)
            else:
                login_api_user_or_401()

            admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
            permission = scope.replace("organization.", "")
            access_or_401(admin_unit, permission)
            set_current_admin_unit(admin_unit)

            return func(*args, **kwargs)

        return wrapped

    return inner_decorator


@marshal_with(ErrorResponseSchema, 400, "Bad Request")
@marshal_with(UnprocessableEntityResponseSchema, 422, "Unprocessable Entity")
@marshal_with(TooManyRequestsResponseSchema, 429, "Too many requests")
class BaseResource(MethodResource):
    decorators = [etag_cache]

    def create_instance(self, schema_cls, **kwargs):
        instance = schema_cls().load(request.json, session=db.session)

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        validate = getattr(instance, "validate", None)
        if callable(validate):
            validate()

        return instance

    def update_instance(self, schema_cls, instance):
        with db.session.no_autoflush:
            instance = schema_cls().load(
                request.json, session=db.session, instance=instance
            )

            validate = getattr(instance, "validate", None)
            if callable(validate):
                validate()

        return instance


def current_token_as_app_or_401():
    if not current_token or not current_token.app_id:  # pragma: no cover
        abort(401)
