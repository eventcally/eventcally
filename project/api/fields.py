from marshmallow import ValidationError, fields

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


class TimezoneDateTimeField(fields.DateTime):
    def __init__(self, format: str | None = None, **kwargs) -> None:
        super().__init__(format, **kwargs)
        self.custom_timezone = kwargs.pop("custom_timezone", None)

    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            if value.tzinfo:
                value = value.astimezone(self.custom_timezone)
            else:
                value = value.replace(tzinfo=self.custom_timezone)

        return super()._serialize(value, attr, obj, **kwargs)

    def deserialize(self, value, attr, data, **kwargs):
        try:
            result = super().deserialize(value, attr, data, **kwargs)
        except ValidationError:
            result = super().deserialize(value + "T00:00:00", attr, data, **kwargs)

        if result and result.tzinfo is None:
            result = self.custom_timezone.localize(result)

        return result


class CustomDateTimeField(TimezoneDateTimeField):
    def __init__(self, format: str | None = None, **kwargs) -> None:
        kwargs["custom_timezone"] = berlin_tz
        super().__init__(format, **kwargs)


class GmtDateTimeField(TimezoneDateTimeField):
    def __init__(self, format: str | None = None, **kwargs) -> None:
        kwargs["custom_timezone"] = gmt_tz
        super().__init__(format, **kwargs)
