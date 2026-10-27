"""apispec 6 renders the Swagger 2.0 document differently from apispec 4; these overrides
keep the published document unchanged (guarded by test_openapi_snapshot)."""

from apispec.ext.marshmallow import MarshmallowPlugin
from apispec.ext.marshmallow.field_converter import (
    make_min_max_attributes,
    make_type_list,
)
from apispec.ext.marshmallow.openapi import OpenAPIConverter


class StableOpenAPIConverter(OpenAPIConverter):
    def schema2jsonschema(self, schema):
        # apispec 6 adds additionalProperties=false for unknown=RAISE schemas,
        # response schemas included; not part of the published contract.
        jsonschema = super().schema2jsonschema(schema)
        jsonschema.pop("additionalProperties", None)
        return jsonschema

    def field2choices(self, field, **kwargs):
        # Swagger 2.0 has no null type; x-nullable already marks the field.
        attributes = super().field2choices(field, **kwargs)
        if None in attributes.get("enum", []):
            attributes["enum"] = [c for c in attributes["enum"] if c is not None]
        return attributes

    def field2range(self, field, ret):
        # apispec 6 serializes the bounds through the field (NumericStr -> "90").
        validators = [
            v
            for v in field.validators
            if hasattr(v, "min") and hasattr(v, "max") and not hasattr(v, "equal")
        ]
        min_attr, max_attr = (
            ("minimum", "maximum")
            if set(make_type_list(ret.get("type"))) & {"number", "integer"}
            else ("x-minimum", "x-maximum")
        )
        return make_min_max_attributes(validators, min_attr, max_attr)

    def field2property(self, field):
        # Swagger 2.0 ignores siblings of $ref (x-nullable would be lost).
        ret = super().field2property(field)
        if "$ref" in ret and len(ret) > 1:
            ret["allOf"] = [{"$ref": ret.pop("$ref")}]
        return ret


class StableMarshmallowPlugin(MarshmallowPlugin):
    Converter = StableOpenAPIConverter
