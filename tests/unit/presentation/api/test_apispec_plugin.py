from apispec import APISpec
from marshmallow import Schema, fields, validate

from project.presentation.api.apispec_plugin import StableMarshmallowPlugin
from project.presentation.api.fields import NumericStr


class ChildSchema(Schema):
    name = fields.Str()


class ParentSchema(Schema):
    rating = fields.Integer(validate=validate.OneOf([0, 10]), allow_none=True)
    latitude = NumericStr(validate=validate.Range(min=-90, max=90))
    count = fields.Integer(validate=validate.Range(min=0, max=5))
    child = fields.Nested(ChildSchema, allow_none=True)
    plain_child = fields.Nested(ChildSchema)


def _definitions():
    spec = APISpec("t", "1", openapi_version="2.0", plugins=[StableMarshmallowPlugin()])
    spec.components.schema("Child", schema=ChildSchema)
    spec.components.schema("Parent", schema=ParentSchema)
    return spec.to_dict()["definitions"]


def test_no_additional_properties():
    assert "additionalProperties" not in _definitions()["Child"]


def test_enum_without_null():
    rating = _definitions()["Parent"]["properties"]["rating"]
    assert rating["enum"] == [0, 10]
    assert rating["x-nullable"] is True


def test_range_bounds_stay_numbers():
    props = _definitions()["Parent"]["properties"]
    assert props["latitude"]["x-minimum"] == -90
    assert props["latitude"]["x-maximum"] == 90
    assert props["count"]["minimum"] == 0
    assert props["count"]["maximum"] == 5


def test_nullable_nested_keeps_all_of():
    props = _definitions()["Parent"]["properties"]
    assert props["child"] == {
        "allOf": [{"$ref": "#/definitions/Child"}],
        "x-nullable": True,
    }
    assert props["plain_child"] == {"$ref": "#/definitions/Child"}
