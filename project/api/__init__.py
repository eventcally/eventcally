from flask_restful import Api
from sqlalchemy.exc import IntegrityError
from psycopg2.errorcodes import UNIQUE_VIOLATION
from werkzeug.exceptions import HTTPException, UnprocessableEntity
from marshmallow import ValidationError
from project.utils import get_localized_scope
from project import app
from flask_marshmallow import Marshmallow
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec


class RestApi(Api):
    def handle_error(self, err):
        from project.api.schemas import (
            ErrorResponseSchema,
            UnprocessableEntityResponseSchema,
        )

        schema = None
        data = {}
        code = 500

        if (
            isinstance(err, IntegrityError)
            and err.orig
            and err.orig.pgcode == UNIQUE_VIOLATION
        ):
            data["name"] = "Unique Violation"
            data[
                "message"
            ] = "An entry with the entered values ​​already exists. Duplicate entries are not allowed."
            code = 400
            schema = ErrorResponseSchema()
        elif isinstance(err, HTTPException):
            data["name"] = err.name
            data["message"] = err.description
            code = err.code

            if (
                isinstance(err, UnprocessableEntity)
                and err.exc
                and isinstance(err.exc, ValidationError)
            ):
                data["name"] = err.name
                data["message"] = err.description
                code = err.code
                schema = UnprocessableEntityResponseSchema()

                if (
                    getattr(err.exc, "args", None)
                    and isinstance(err.exc.args, tuple)
                    and len(err.exc.args) > 0
                ):
                    arg = err.exc.args[0]
                    if isinstance(arg, dict):
                        errors = []
                        for field, messages in arg.items():
                            if isinstance(messages, list):
                                for message in messages:
                                    error = {"field": field, "message": message}
                                    errors.append(error)

                        if len(errors) > 0:
                            data["errors"] = errors
            else:
                schema = ErrorResponseSchema()

        # Call default error handler that propagates error further
        try:
            super().handle_error(err)
        except Exception:
            if not schema:
                raise

        return schema.dump(data), code


scope_list = [
    "organizer:write",
    "place:write",
    "event:write",
]
scopes = {k: get_localized_scope(k) for v, k in enumerate(scope_list)}

rest_api = RestApi(app, "/api/v1", catch_all_404s=True)
marshmallow = Marshmallow(app)
marshmallow_plugin = MarshmallowPlugin()
app.config.update(
    {
        "APISPEC_SPEC": APISpec(
            title="Oveda API",
            version="0.1.0",
            plugins=[marshmallow_plugin],
            openapi_version="2.0",
            info=dict(
                description="This API provides endpoints to interact with the Oveda data."
            ),
        ),
    }
)

api_docs = FlaskApiSpec(app)


def enum_to_properties(self, field, **kwargs):
    """
    Add an OpenAPI extension for marshmallow_enum.EnumField instances
    """
    import marshmallow_enum

    if isinstance(field, marshmallow_enum.EnumField):
        return {"type": "string", "enum": [m.name for m in field.enum]}
    return {}


def add_api_resource(resource, url, endpoint):
    rest_api.add_resource(resource, url, endpoint=endpoint)
    api_docs.register(resource, endpoint=endpoint)


marshmallow_plugin.converter.add_attribute_function(enum_to_properties)

import project.api.event.resources
import project.api.event_category.resources
import project.api.event_date.resources
import project.api.event_reference.resources
import project.api.dump.resources
import project.api.organization.resources
import project.api.organizer.resources
import project.api.place.resources
