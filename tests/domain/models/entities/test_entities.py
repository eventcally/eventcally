import datetime

import pytest
from pydantic import ValidationError

from project.domain.models.entities.actor import Actor
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.types.unset import unset


class TestActor:
    def test_default_all_none(self):
        actor = Actor()
        assert actor.user_id is None
        assert actor.app_installation_id is None

    def test_with_user_id(self):
        actor = Actor(user_id=42)
        assert actor.user_id == 42
        assert actor.app_installation_id is None

    def test_with_app_installation_id(self):
        actor = Actor(app_installation_id=99)
        assert actor.app_installation_id == 99
        assert actor.user_id is None

    def test_is_frozen(self):
        actor = Actor(user_id=1)
        with pytest.raises(ValidationError):
            actor.user_id = 2


class TestEventDateEntity:
    def test_required_fields(self):
        now = datetime.datetime(2024, 6, 1, 10, 0, 0)
        entity = EventDateEntity(id=1, start=now)
        assert entity.id == 1
        assert entity.start == now

    def test_end_defaults_to_none(self):
        now = datetime.datetime(2024, 6, 1, 10, 0, 0)
        entity = EventDateEntity(id=1, start=now)
        assert entity.end is None

    def test_allday_defaults_to_false(self):
        now = datetime.datetime(2024, 6, 1, 10, 0, 0)
        entity = EventDateEntity(id=1, start=now)
        assert entity.allday is False

    def test_with_end_and_allday(self):
        start = datetime.datetime(2024, 6, 1, 0, 0, 0)
        end = datetime.datetime(2024, 6, 1, 23, 59, 59)
        entity = EventDateEntity(id=2, start=start, end=end, allday=True)
        assert entity.end == end
        assert entity.allday is True


class TestImageEntityFromValueObject:
    def test_returns_none_when_value_object_is_none(self):
        result = ImageEntity.from_value_object(None)
        assert result is None

    def test_returns_image_entity_when_value_object_provided(self):
        vo = ImageValueObject(data=b"bytes", encoding_format="image/png")
        result = ImageEntity.from_value_object(vo)
        assert isinstance(result, ImageEntity)

    def test_maps_data(self):
        vo = ImageValueObject(data=b"raw_data", encoding_format="image/jpeg")
        result = ImageEntity.from_value_object(vo)
        assert result.data == b"raw_data"

    def test_maps_encoding_format(self):
        vo = ImageValueObject(data=b"", encoding_format="image/gif")
        result = ImageEntity.from_value_object(vo)
        assert result.encoding_format == "image/gif"

    def test_maps_copyright_text(self):
        vo = ImageValueObject(
            data=b"", encoding_format="image/png", copyright_text="(c) 2024"
        )
        result = ImageEntity.from_value_object(vo)
        assert result.copyright_text == "(c) 2024"

    def test_maps_license_id(self):
        vo = ImageValueObject(data=b"", encoding_format="image/png", license_id=5)
        result = ImageEntity.from_value_object(vo)
        assert result.license_id == 5

    def test_copyright_text_defaults_none(self):
        vo = ImageValueObject(data=b"", encoding_format="image/png")
        result = ImageEntity.from_value_object(vo)
        assert result.copyright_text is None
        assert result.license_id is None


class TestImageEntityFromNullableUnsetableValueObject:
    def test_returns_unset_when_unset(self):
        result = ImageEntity.from_nullable_unsetable_value_object(unset)
        assert result is unset

    def test_returns_none_when_none(self):
        result = ImageEntity.from_nullable_unsetable_value_object(None)
        assert result is None

    def test_returns_image_entity_when_value_object(self):
        vo = ImageValueObject(data=b"data", encoding_format="image/jpeg")
        result = ImageEntity.from_nullable_unsetable_value_object(vo)
        assert isinstance(result, ImageEntity)
        assert result.data == b"data"
