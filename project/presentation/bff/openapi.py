import json
from typing import Any

from pydantic.json_schema import models_json_schema

from project.presentation.bff.schemas import ErrorResponse, ValidationErrorResponse

_REF = "#/components/schemas/{model}"


def _ref(name: str) -> dict:
    return {"$ref": _REF.format(model=name)}


def _parameters(model) -> list[dict]:
    schema = model.model_json_schema()
    required = set(schema.get("required", []))
    return [
        {
            "name": name,
            "in": "query",
            "required": name in required,
            "schema": {k: v for k, v in prop.items() if k != "title"},
        }
        for name, prop in schema["properties"].items()
    ]


def build_openapi() -> dict[str, Any]:
    """Build the OpenAPI 3.1 document from the registered BFF routes.

    Needs neither an app nor any environment variables.
    """
    import project.presentation.bff  # noqa: F401  (imports the routes, fills ROUTES)
    from project.presentation.bff.routing import ROUTES

    models: list = [ErrorResponse, ValidationErrorResponse]
    for route in ROUTES:
        models.append(route.response_model)
        if route.body_model:
            models.append(route.body_model)
    unique = list({m: None for m in models})

    _, defs = models_json_schema(
        [(m, "serialization") for m in unique], ref_template=_REF
    )

    paths: dict[str, dict] = {}
    for route in sorted(ROUTES, key=lambda r: (r.full_rule, r.method)):
        responses = {
            "200": {
                "description": "OK",
                "content": {
                    "application/json": {"schema": _ref(route.response_model.__name__)}
                },
            },
            "401": {
                "description": "Unauthorized",
                "content": {"application/json": {"schema": _ref("ErrorResponse")}},
            },
            "403": {
                "description": "Forbidden",
                "content": {"application/json": {"schema": _ref("ErrorResponse")}},
            },
            "422": {
                "description": "Unprocessable Entity",
                "content": {
                    "application/json": {"schema": _ref("ValidationErrorResponse")}
                },
            },
        }
        operation: dict[str, Any] = {
            "operationId": route.endpoint.replace(".", "_"),
            "responses": responses,
        }
        if route.summary:
            operation["summary"] = route.summary
        if route.query_model:
            operation["parameters"] = _parameters(route.query_model)
        if route.body_model:
            operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {"schema": _ref(route.body_model.__name__)}
                },
            }
        paths.setdefault(route.full_rule, {})[route.method] = operation

    return {
        "openapi": "3.1.0",
        "info": {"title": "EventCally BFF", "version": "1.0.0"},
        "paths": paths,
        "components": {"schemas": defs.get("$defs", {})},
    }


if __name__ == "__main__":
    print(json.dumps(build_openapi(), indent=2, sort_keys=True))
