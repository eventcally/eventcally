import functools
import re
import typing
from dataclasses import dataclass
from typing import Optional, Type

from flask import Blueprint, jsonify, request
from pydantic import BaseModel
from werkzeug.wrappers import Response


@dataclass(frozen=True)
class RouteSpec:
    blueprint: Blueprint
    rule: str
    method: str
    endpoint: str
    query_model: Optional[Type[BaseModel]]
    body_model: Optional[Type[BaseModel]]
    response_model: Optional[Type[BaseModel]]
    summary: Optional[str]
    status: int = 200

    @property
    def full_rule(self) -> str:
        """The URL rule including the prefixes of all parent blueprints."""
        prefix = _blueprint_prefix(self.blueprint)
        return prefix + self.rule

    @property
    def path_params(self) -> tuple[tuple[str, str], ...]:
        """The `(name, converter)` pairs of the rule, e.g. `("id", "int")`."""
        return tuple(
            (name, converter or "string")
            for converter, name in _RULE_PARAM.findall(self.full_rule)
        )

    @property
    def openapi_rule(self) -> str:
        """`full_rule` in OpenAPI notation: `<int:id>` becomes `{id}`."""
        return _RULE_PARAM.sub(lambda m: "{" + m.group(2) + "}", self.full_rule)


_RULE_PARAM = re.compile(r"<(?:(\w+):)?(\w+)>")

ROUTES: list[RouteSpec] = []

# Nested blueprints are registered by `init_bff`; the chain is resolved lazily so
# the spec can be built without an app.
_PARENTS: dict[Blueprint, Blueprint] = {}


def set_parent(child: Blueprint, parent: Blueprint) -> None:
    _PARENTS[child] = parent


def _blueprint_prefix(bp: Blueprint) -> str:
    prefix = bp.url_prefix or ""
    parent = _PARENTS.get(bp)
    if parent is not None:
        return _blueprint_prefix(parent) + prefix
    return prefix


def _is_list_annotation(annotation) -> bool:
    if typing.get_origin(annotation) is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        return len(args) == 1 and _is_list_annotation(args[0])
    return typing.get_origin(annotation) is list


def _query_args(model: Type[BaseModel]) -> dict:
    """The query string as a dict; `list[...]` fields read all repeated keys."""
    args = request.args.to_dict()
    for name, field in model.model_fields.items():
        if _is_list_annotation(field.annotation):
            values = request.args.getlist(name)
            if values:
                args[name] = values
            else:
                args.pop(name, None)
    return args


def bff_route(
    bp: Blueprint,
    rule: str,
    *,
    method: str = "GET",
    query: Optional[Type[BaseModel]] = None,
    body: Optional[Type[BaseModel]] = None,
    response: Optional[Type[BaseModel]] = None,
    status: Optional[int] = None,
    summary: Optional[str] = None,
):
    """Register a JSON view on `bp` and record it for the OpenAPI document.

    The query string / JSON body are validated with the given pydantic models and
    passed to the view as the `query=` / `body=` keyword arguments. The return value
    is validated through `response` and serialized to JSON; without a `response` the
    route answers `204 No Content`. A pydantic `ValidationError` propagates to the BFF
    error handler (422).
    """
    if status is None:
        status = 200 if response is not None else 204

    def decorator(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            if query is not None:
                kwargs["query"] = query.model_validate(_query_args(query))
            if body is not None:
                kwargs["body"] = body.model_validate(request.get_json(silent=True))

            result = view(*args, **kwargs)
            if isinstance(result, Response):
                # e.g. the 401 of an auth decorator in front of the view
                return result
            if response is None:
                return "", status
            payload = response.model_validate(result).model_dump(mode="json")
            return jsonify(payload), status

        bp.add_url_rule(rule, view_func=wrapper, methods=[method])
        ROUTES.append(
            RouteSpec(
                blueprint=bp,
                rule=rule,
                method=method.lower(),
                endpoint=f"{bp.name}.{view.__name__}",
                query_model=query,
                body_model=body,
                response_model=response,
                summary=summary,
                status=status,
            )
        )
        return wrapper

    return decorator
