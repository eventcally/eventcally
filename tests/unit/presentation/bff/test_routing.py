import pytest
from flask import Blueprint, Flask
from pydantic import BaseModel, ValidationError

from project.presentation.bff import routing
from project.presentation.bff.routing import ROUTES, bff_route, set_parent


class Params(BaseModel):
    n: int


class Out(BaseModel):
    doubled: int


@pytest.fixture
def bp():
    before = len(ROUTES)
    bp = Blueprint("t_bff", __name__, url_prefix="/t")
    yield bp
    del ROUTES[before:]
    routing._PARENTS.pop(bp, None)


def test_validates_query_and_dumps_response(bp):
    @bff_route(bp, "/double", query=Params, response=Out, summary="Double")
    def double(query: Params):
        return {"doubled": query.n * 2}

    app = Flask(__name__)
    app.register_blueprint(bp)

    response = app.test_client().get("/t/double?n=4")

    assert response.status_code == 200
    assert response.json == {"doubled": 8}


def test_invalid_query_raises_validation_error(bp):
    @bff_route(bp, "/double", query=Params, response=Out)
    def double(query: Params):  # pragma: no cover
        return {"doubled": 0}

    app = Flask(__name__)
    app.register_blueprint(bp)
    app.config["PROPAGATE_EXCEPTIONS"] = True

    with pytest.raises(ValidationError):
        app.test_client().get("/t/double?n=x")


def test_records_route_spec_with_parent_prefix(bp):
    @bff_route(bp, "/double", query=Params, response=Out, summary="Double")
    def double(query: Params):  # pragma: no cover
        return {"doubled": 0}

    parent = Blueprint("t_parent", __name__, url_prefix="/p")
    set_parent(bp, parent)

    spec = ROUTES[-1]
    assert spec.full_rule == "/p/t/double"
    assert spec.method == "get"
    assert spec.query_model is Params
    assert spec.response_model is Out
    assert spec.summary == "Double"


class Body(BaseModel):
    n: int


def test_body_and_response_passthrough(bp):
    from werkzeug.wrappers import Response

    @bff_route(bp, "/echo", method="POST", body=Body, response=Out, status=201)
    def echo(body: Body):
        return {"doubled": body.n * 2}

    @bff_route(bp, "/raw", response=Out)
    def raw():
        return Response("teapot", status=418)

    app = Flask(__name__)
    app.register_blueprint(bp)
    client = app.test_client()

    created = client.post("/t/echo", json={"n": 2})
    assert created.status_code == 201
    assert created.json == {"doubled": 4}
    assert client.get("/t/raw").status_code == 418

    from project.presentation.bff.openapi import build_openapi

    set_parent(bp, Blueprint("t_root", __name__, url_prefix="/r"))
    operation = build_openapi()["paths"]["/r/t/echo"]["post"]
    assert operation["requestBody"]["required"] is True


def test_path_params_and_no_content(bp):
    @bff_route(bp, "/items/<int:id>", method="DELETE")
    def remove(id: int):
        assert isinstance(id, int)

    @bff_route(bp, "/items/<int:id>/tags/<tag>", response=Out)
    def tag(id: int, tag: str):
        return {"doubled": id}

    app = Flask(__name__)
    app.register_blueprint(bp)
    client = app.test_client()

    deleted = client.delete("/t/items/3")
    assert deleted.status_code == 204
    assert deleted.data == b""
    assert client.get("/t/items/3/tags/x").json == {"doubled": 3}

    remove_spec, tag_spec = ROUTES[-2:]
    assert remove_spec.status == 204
    assert remove_spec.response_model is None
    assert remove_spec.openapi_rule == "/t/items/{id}"
    assert remove_spec.path_params == (("id", "int"),)
    assert tag_spec.status == 200
    assert tag_spec.openapi_rule == "/t/items/{id}/tags/{tag}"
    assert tag_spec.path_params == (("id", "int"), ("tag", "string"))
