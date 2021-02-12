from marshmallow import ValidationError, fields

from project.dateutils import berlin_tz


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


class CustomDateTimeField(fields.DateTime):
    def deserialize(self, value, attr, data, **kwargs):
        result = super().deserialize(value, attr, data, **kwargs)

        if result and result.tzinfo is None:
            result = berlin_tz.localize(result)

        return result
