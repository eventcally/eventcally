from flask import request
from flask_apispec.views import MethodResource
from functools import wraps


def etag_cache(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.add_etag()
        return response.make_conditional(request)

    return wrapper


class BaseResource(MethodResource):
    decorators = [etag_cache]
