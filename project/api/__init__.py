from apispec import APISpec
from apispec.exceptions import DuplicateComponentNameError
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import url_for
from flask_apispec.extension import FlaskApiSpec
from flask_marshmallow import Marshmallow
from flask_restful import Api
from marshmallow import ValidationError
from psycopg2.errorcodes import CHECK_VIOLATION, UNIQUE_VIOLATION
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, UnprocessableEntity

from project import app
from project.utils import get_localized_scope


class RestApi(Api):
    def handle_error(self, err):
        from project.api.schemas import (
            ErrorResponseSchema,
            UnprocessableEntityResponseSchema,
        )

        schema = None
        data = {}
        code = 500

        if isinstance(err, IntegrityError) and err.orig:
            if err.orig.pgcode == UNIQUE_VIOLATION:
                data["name"] = "Unique Violation"
                data[
                    "message"
                ] = "An entry with the entered values ​​already exists. Duplicate entries are not allowed."
            elif err.orig.pgcode == CHECK_VIOLATION:
                data["name"] = "Check Violation"

                if hasattr(err.orig, "message") and getattr(err.orig, "message", None):
                    data["message"] = err.orig.message
                else:
                    data["message"] = "Action violates database constraint."

            else:
                data["name"] = "Integrity Error"
                data["message"] = "Action violates database integrity."
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
                self.fill_validation_data(err.exc, data)

            else:
                schema = ErrorResponseSchema()
        elif isinstance(err, ValidationError):
            data["name"] = "Unprocessable Entity"
            data[
                "message"
            ] = "The request was well-formed but was unable to be followed due to semantic errors."
            code = 422
            schema = UnprocessableEntityResponseSchema()
            self.fill_validation_data(err, data)

        # Call default error handler that propagates error further
        try:
            super().handle_error(err)
        except Exception:
            if not schema:
                raise

        return schema.dump(data), code

    def fill_validation_data(self, err: ValidationError, data: dict):
        if (
            getattr(err, "args", None)
            and isinstance(err.args, tuple)
            and len(err.args) > 0
        ):
            arg = err.args[0]
            if isinstance(arg, dict):
                errors = []
                for field, messages in arg.items():
                    if isinstance(messages, list):
                        for message in messages:
                            error = {"field": field, "message": message}
                            errors.append(error)

                if len(errors) > 0:
                    data["errors"] = errors


scope_list = [
    "openid",
    "profile",
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


def add_oauth2_scheme_with_transport(insecure: bool):
    if insecure:
        authorizationUrl = url_for("authorize", _external=True)
        tokenUrl = url_for("issue_token", _external=True)
    else:
        authorizationUrl = url_for("authorize", _external=True, _scheme="https")
        tokenUrl = url_for("issue_token", _external=True, _scheme="https")

    oauth2_scheme = {
        "type": "oauth2",
        "authorizationUrl": authorizationUrl,
        "tokenUrl": tokenUrl,
        "flow": "accessCode",
        "scopes": scopes,
    }

    try:
        api_docs.spec.components.security_scheme("oauth2", oauth2_scheme)
    except DuplicateComponentNameError:  # pragma: no cover
        pass


marshmallow_plugin.converter.add_attribute_function(enum_to_properties)

import project.api.dump.resources
import project.api.event.resources
import project.api.event_category.resources
import project.api.event_date.resources
import project.api.event_reference.resources
import project.api.organization.resources
import project.api.organizer.resources
import project.api.place.resources
