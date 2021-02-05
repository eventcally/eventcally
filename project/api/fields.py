from marshmallow import fields, ValidationError


class NumericStr(fields.String):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None

        return str(value)

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            return float(value)
        except ValueError as error:
            raise ValidationError("Must be a numeric value.") from error
