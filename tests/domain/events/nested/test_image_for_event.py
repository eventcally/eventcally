from project.domain.events.nested.image_for_event import ImageForEvent
from project.domain.models.entities.image_entity import ImageEntity


def _make_image_entity():
    return ImageEntity.model_construct(
        id=42,
        hash=12345,
        data=b"image_bytes",
        encoding_format="image/jpeg",
        copyright_text="(c) Test",
        license_id=7,
    )


class TestImageForEventFromImageEntity:
    def test_returns_none_when_entity_is_none(self):
        result = ImageForEvent.from_image_entity(None)
        assert result is None

    def test_returns_image_for_event_when_entity_provided(self):
        entity = _make_image_entity()
        result = ImageForEvent.from_image_entity(entity)
        assert isinstance(result, ImageForEvent)

    def test_maps_id(self):
        entity = _make_image_entity()
        result = ImageForEvent.from_image_entity(entity)
        assert result.id == 42

    def test_maps_hash(self):
        entity = _make_image_entity()
        result = ImageForEvent.from_image_entity(entity)
        assert result.hash == 12345

    def test_maps_encoding_format(self):
        entity = _make_image_entity()
        result = ImageForEvent.from_image_entity(entity)
        assert result.encoding_format == "image/jpeg"

    def test_maps_copyright_text(self):
        entity = _make_image_entity()
        result = ImageForEvent.from_image_entity(entity)
        assert result.copyright_text == "(c) Test"

    def test_maps_license_id(self):
        entity = _make_image_entity()
        result = ImageForEvent.from_image_entity(entity)
        assert result.license_id == 7

    def test_copyright_text_none_when_not_set(self):
        entity = ImageEntity.model_construct(
            id=1,
            hash=0,
            data=b"",
            encoding_format="image/png",
            copyright_text=None,
            license_id=None,
        )
        result = ImageForEvent.from_image_entity(entity)
        assert result.copyright_text is None
        assert result.license_id is None
