from flask import request
from flask_apispec import marshal_with
from flask_apispec.views import MethodResource
from functools import wraps
from project.api.schemas import ErrorResponseSchema, UnprocessableEntityResponseSchema


def etag_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.add_etag()
        return response.make_conditional(request)

    return wrapper


@marshal_with(ErrorResponseSchema, 400, "Bad Request")
@marshal_with(UnprocessableEntityResponseSchema, 422, "Unprocessable Entity")
class BaseResource(MethodResource):
    decorators = [etag_cache]
