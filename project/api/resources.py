from functools import wraps

from authlib.oauth2 import OAuth2Error
from flask import request
from flask_apispec import marshal_with
from flask_apispec.annotations import annotate
from flask_apispec.views import MethodResource
from flask_wtf.csrf import validate_csrf

from project import app, csrf, db
from project.api.schemas import ErrorResponseSchema, UnprocessableEntityResponseSchema
from project.oauth2 import require_oauth


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


def require_api_access(scopes=None):
    def inner_decorator(func):
        def wrapped(*args, **kwargs):  # see authlib ResourceProtector#__call__
            try:  # pragma: no cover
                try:
                    require_oauth.acquire_token(scopes)
                except OAuth2Error as error:
                    require_oauth.raise_error_response(error)
            except Exception as e:
                if app.config["API_READ_ANONYM"]:
                    return func(*args, **kwargs)
                if not is_internal_request():
                    raise e
            return func(*args, **kwargs)

        scope_list = scopes if type(scopes) is list else [scopes] if scopes else list()
        security = [{"oauth2AuthCode": scope_list}]

        if not scope_list:
            security.append(
                {
                    "oauth2ClientCredentials": scope_list,
                }
            )

        annotate(
            wrapped,
            "docs",
            [{"security": security}],
        )
        return wrapped

    return inner_decorator


@marshal_with(ErrorResponseSchema, 400, "Bad Request")
@marshal_with(UnprocessableEntityResponseSchema, 422, "Unprocessable Entity")
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
