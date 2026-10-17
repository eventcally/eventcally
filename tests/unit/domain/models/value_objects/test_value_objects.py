import datetime
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.models.value_objects.webhook_value_object import WebhookValueObject


class TestImageValueObject:
    def test_required_fields(self):
        vo = ImageValueObject(data=b"bytes", encoding_format="image/png")
        assert vo.data == b"bytes"
        assert vo.encoding_format == "image/png"

    def test_optional_fields_default_none(self):
        vo = ImageValueObject(data=b"", encoding_format="image/jpeg")
        assert vo.copyright_text is None
        assert vo.license_id is None

    def test_with_all_fields(self):
        vo = ImageValueObject(
            data=b"img",
            encoding_format="image/webp",
            copyright_text="(c)",
            license_id=3,
        )
        assert vo.copyright_text == "(c)"
        assert vo.license_id == 3


class TestLocationValueObject:
    def test_all_fields_default_to_none(self):
        vo = LocationValueObject()
        assert vo.street is None
        assert vo.postalCode is None
        assert vo.city is None
        assert vo.state is None
        assert vo.country is None
        assert vo.latitude is None
        assert vo.longitude is None

    def test_with_city_and_country(self):
        vo = LocationValueObject(city="Berlin", country="DE")
        assert vo.city == "Berlin"
        assert vo.country == "DE"

    def test_with_coordinates(self):
        vo = LocationValueObject(latitude=52.5, longitude=13.4)
        assert vo.latitude == 52.5
        assert vo.longitude == 13.4


class TestWebhookValueObject:
    def test_required_url(self):
        vo = WebhookValueObject(url="https://example.com/hook")
        assert vo.url == "https://example.com/hook"

    def test_optional_fields_defaults(self):
        vo = WebhookValueObject(url="https://example.com")
        assert vo.secret is None
        assert vo.disabled is False
        assert vo.event_types == set()

    def test_with_secret_and_event_types(self):
        vo = WebhookValueObject(
            url="https://example.com",
            secret="my_secret",
            disabled=True,
            event_types=["event.created", "event.deleted"],
        )
        assert vo.secret == "my_secret"
        assert vo.disabled is True
        assert vo.event_types == {"event.created", "event.deleted"}


class TestEventDateDefinitionValueObject:
    def test_required_start(self):
        start = datetime.datetime(2024, 6, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
        vo = EventDateDefinitionValueObject(start=start)
        assert vo.start == start

    def test_optional_defaults(self):
        start = datetime.datetime(2024, 6, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
        vo = EventDateDefinitionValueObject(start=start)
        assert vo.end is None
        assert vo.allday is False
        assert vo.recurrence_rule is None

    def test_with_all_fields(self):
        start = datetime.datetime(2024, 6, 1, 10, 0, tzinfo=ZoneInfo("UTC"))
        end = datetime.datetime(2024, 6, 1, 12, 0, tzinfo=ZoneInfo("UTC"))
        vo = EventDateDefinitionValueObject(
            start=start,
            end=end,
            allday=False,
            recurrence_rule="FREQ=WEEKLY;COUNT=3",
        )
        assert vo.end == end
        assert vo.allday is False
        assert vo.recurrence_rule == "FREQ=WEEKLY;COUNT=3"

    def test_rejects_fixed_offset_timezone(self):
        with pytest.raises(ValidationError, match="IANA timezone"):
            EventDateDefinitionValueObject(
                start=datetime.datetime(2024, 6, 1, 10, 0, tzinfo=datetime.timezone.utc)
            )


class TestEventDateDefinitionValueObjectCompare:
    @property
    def berlin_tz(self):
        from project.domain.dateutils import berlin_tz

        return berlin_tz

    def _canonical(self):
        # The database's canonical, Berlin-widened representation of an
        # all-day event on 2024-06-01: 00:00:00 ... 23:59:59 Berlin.
        return EventDateDefinitionValueObject(
            start=datetime.datetime(2024, 6, 1, 0, 0, 0, tzinfo=self.berlin_tz),
            end=datetime.datetime(2024, 6, 1, 23, 59, 59, tzinfo=self.berlin_tz),
            allday=True,
        )

    def test_form_shape_without_seconds_compares_equal(self):
        # The edit form's time widget has no seconds field, so an untouched
        # all-day end posts back as 23:59:00 instead of 23:59:59.
        old = self._canonical()
        new = EventDateDefinitionValueObject(
            start=datetime.datetime(2024, 6, 1, 0, 0, 0, tzinfo=self.berlin_tz),
            end=datetime.datetime(2024, 6, 1, 23, 59, 0, tzinfo=self.berlin_tz),
            allday=True,
        )
        assert old == new

    def test_api_shape_without_end_compares_equal(self):
        old = self._canonical()
        new = EventDateDefinitionValueObject(
            start=datetime.datetime(2024, 6, 1, 0, 0, 0, tzinfo=self.berlin_tz),
            end=None,
            allday=True,
        )
        assert old == new

    def test_different_day_compares_unequal(self):
        old = self._canonical()
        new = EventDateDefinitionValueObject(
            start=datetime.datetime(2024, 6, 2, 0, 0, 0, tzinfo=self.berlin_tz),
            end=datetime.datetime(2024, 6, 2, 23, 59, 59, tzinfo=self.berlin_tz),
            allday=True,
        )
        assert old != new

    def test_recurrence_rule_crlf_compares_equal_to_lf(self):
        start = datetime.datetime(2026, 4, 6, 11, 0, tzinfo=self.berlin_tz)
        rule = "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260504"
        old = EventDateDefinitionValueObject(start=start, recurrence_rule=rule)
        new = EventDateDefinitionValueObject(
            start=start, recurrence_rule=rule.replace("\n", "\r\n")
        )
        assert old == new
        assert new.recurrence_rule == rule

    def test_empty_recurrence_rule_compares_equal_to_none(self):
        start = datetime.datetime(2026, 4, 6, 11, 0, tzinfo=self.berlin_tz)
        old = EventDateDefinitionValueObject(start=start)
        new = EventDateDefinitionValueObject(start=start, recurrence_rule="")
        assert old == new

    def test_changed_recurrence_rule_compares_unequal(self):
        old = self._canonical()
        new = EventDateDefinitionValueObject(
            start=old.start,
            end=old.end,
            allday=True,
            recurrence_rule="FREQ=WEEKLY;COUNT=3",
        )
        assert old != new

    def test_allday_mismatch_compares_unequal(self):
        old = self._canonical()
        new = EventDateDefinitionValueObject(
            start=old.start,
            end=old.end,
            allday=False,
        )
        assert old != new

    def test_timed_definitions_59_seconds_apart_compare_unequal(self):
        # The all-day fallback must not soften comparison for timed definitions.
        old = EventDateDefinitionValueObject(
            start=datetime.datetime(2024, 6, 1, 10, 0, 0, tzinfo=self.berlin_tz),
        )
        new = EventDateDefinitionValueObject(
            start=datetime.datetime(2024, 6, 1, 10, 0, 59, tzinfo=self.berlin_tz),
        )
        assert old != new
