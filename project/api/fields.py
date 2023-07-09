from marshmallow import ValidationError, fields
from marshmallow_sqlalchemy import fields as msfields

from project.dateutils import berlin_tz, gmt_tz


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
    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            value = value.astimezone(berlin_tz)

        return super()._serialize(value, attr, obj, **kwargs)

    def deserialize(self, value, attr, data, **kwargs):
        result = super().deserialize(value, attr, data, **kwargs)

        if result and result.tzinfo is None:
            result = berlin_tz.localize(result)

        return result


class GmtDateTimeField(fields.DateTime):
    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            value = value.replace(tzinfo=gmt_tz)

        return super()._serialize(value, attr, obj, **kwargs)

    def deserialize(self, value, attr, data, **kwargs):
        result = super().deserialize(value, attr, data, **kwargs)

        if result and result.tzinfo is None:
            result = gmt_tz.localize(result)

        return result


class Owned(msfields.Nested):
    def _deserialize(self, *args, **kwargs):
        if (
            not self.root.transient
            and hasattr(self.schema, "instance")
            and self.schema.instance is None
            and self.root.instance
            and hasattr(self.root.instance, self.name)
        ):
            self.schema.instance = getattr(self.root.instance, self.name, None)
        return super()._deserialize(*args, **kwargs)
