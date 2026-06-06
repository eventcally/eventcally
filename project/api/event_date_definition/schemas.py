from dateutil.rrule import rrulestr
from marshmallow import ValidationError, fields, post_load

from project.api.fields import CustomDateTimeField
from project.api.schemas import IdSchemaMixin, PlainBaseSchema, SQLAlchemyBaseSchema
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.models import EventDateDefinition


class EventDateDefinitionModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = EventDateDefinition
        load_instance = True


class EventDateDefinitionIdSchema(EventDateDefinitionModelSchema, IdSchemaMixin):
    pass


def validate_recurrence_rule(recurrence_rule):
    try:
        rrulestr(recurrence_rule, forceset=True)
    except Exception as e:
        raise ValidationError(str(e))


class EventDateDefinitionBaseSchemaMixin(object):
    start = CustomDateTimeField(
        required=True,
        metadata={
            "description": "When the event will take place.  If the event takes place regularly, enter when the first date will begin."
        },
    )
    end = CustomDateTimeField(
        metadata={
            "description": "When the event will end. An event can last a maximum of 180 days. If the event takes place regularly, enter when the first date will end."
        },
    )
    allday = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is an all-day event."},
    )
    recurrence_rule = fields.Str(
        validate=validate_recurrence_rule,
        metadata={
            "description": "If the event takes place regularly. Format: RFC 5545."
        },
    )


class EventDateDefinitionSchema(
    EventDateDefinitionIdSchema, EventDateDefinitionBaseSchemaMixin
):
    pass


class EventDateDefinitionDumpSchema(
    EventDateDefinitionIdSchema, EventDateDefinitionBaseSchemaMixin
):
    pass


class EventDateDefinitionWriteSchemaMixin(object):
    pass


class EventDateDefinitionPlainSchema(PlainBaseSchema):
    start = CustomDateTimeField(
        required=True,
        metadata={
            "description": "When the event will take place.  If the event takes place regularly, enter when the first date will begin."
        },
    )
    end = CustomDateTimeField(
        load_default=None,
        metadata={
            "description": "When the event will end. An event can last a maximum of 180 days. If the event takes place regularly, enter when the first date will end."
        },
    )
    allday = fields.Bool(
        load_default=False,
        metadata={"description": "If the event is an all-day event."},
    )
    recurrence_rule = fields.Str(
        load_default=None,
        validate=validate_recurrence_rule,
        metadata={
            "description": "If the event takes place regularly. Format: RFC 5545."
        },
    )

    @post_load
    def make_instance(self, data, **kwargs):
        return EventDateDefinitionValueObject(**data)
