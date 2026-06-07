import datetime

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
        assert vo.event_types == []

    def test_with_secret_and_event_types(self):
        vo = WebhookValueObject(
            url="https://example.com",
            secret="my_secret",
            disabled=True,
            event_types=["event.created", "event.deleted"],
        )
        assert vo.secret == "my_secret"
        assert vo.disabled is True
        assert vo.event_types == ["event.created", "event.deleted"]


class TestEventDateDefinitionValueObject:
    def test_required_start(self):
        start = datetime.datetime(2024, 6, 1, 10, 0)
        vo = EventDateDefinitionValueObject(start=start)
        assert vo.start == start

    def test_optional_defaults(self):
        start = datetime.datetime(2024, 6, 1, 10, 0)
        vo = EventDateDefinitionValueObject(start=start)
        assert vo.end is None
        assert vo.allday is False
        assert vo.recurrence_rule is None

    def test_with_all_fields(self):
        start = datetime.datetime(2024, 6, 1, 10, 0)
        end = datetime.datetime(2024, 6, 1, 12, 0)
        vo = EventDateDefinitionValueObject(
            start=start,
            end=end,
            allday=True,
            recurrence_rule="FREQ=WEEKLY;COUNT=3",
        )
        assert vo.end == end
        assert vo.allday is True
        assert vo.recurrence_rule == "FREQ=WEEKLY;COUNT=3"
