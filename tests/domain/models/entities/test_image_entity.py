from typing import Optional

from project.domain.models.entities.image_entity import ImageEntity
from project.domain.types.object_id import ObjectId


def _make_image(
    data: bytes,
    encoding_format: str = "image/png",
    copyright_text: Optional[str] = None,
    license_id: Optional[ObjectId] = None,
) -> ImageEntity:
    return ImageEntity.model_construct(
        id=1,
        hash=0,
        data=data,
        encoding_format=encoding_format,
        copyright_text=copyright_text,
        license_id=license_id,
    )


class TestImageEntityCompare:
    def test_returns_true_when_all_fields_match(self):
        a = _make_image(b"same", "image/png", "me", 10)
        b = _make_image(b"same", "image/png", "me", 10)
        assert ImageEntity.compare(a, b) is True

    def test_returns_false_when_data_differs(self):
        a = _make_image(b"foo")
        b = _make_image(b"bar")
        assert ImageEntity.compare(a, b) is False

    def test_returns_false_when_encoding_format_differs(self):
        a = _make_image(b"data", "image/png")
        b = _make_image(b"data", "image/jpeg")
        assert ImageEntity.compare(a, b) is False

    def test_returns_false_when_copyright_text_differs(self):
        a = _make_image(b"data", "image/png", "alice")
        b = _make_image(b"data", "image/png", "bob")
        assert ImageEntity.compare(a, b) is False

    def test_returns_false_when_license_id_differs(self):
        a = _make_image(b"data", "image/png", "me", 1)
        b = _make_image(b"data", "image/png", "me", 2)
        assert ImageEntity.compare(a, b) is False

    def test_ignores_hash(self):
        a = ImageEntity.model_construct(
            id=1,
            hash=1,
            data=b"x",
            encoding_format="image/png",
            copyright_text=None,
            license_id=None,
        )
        b = ImageEntity.model_construct(
            id=2,
            hash=99,
            data=b"x",
            encoding_format="image/png",
            copyright_text=None,
            license_id=None,
        )
        assert ImageEntity.compare(a, b) is True

    def test_equal_when_both_optional_fields_are_none(self):
        a = _make_image(b"data")
        b = _make_image(b"data")
        assert ImageEntity.compare(a, b) is True

    def test_returns_false_when_old_is_none(self):
        b = _make_image(b"data")
        assert ImageEntity.compare(None, b) is False

    def test_returns_false_when_new_is_none(self):
        a = _make_image(b"data")
        assert ImageEntity.compare(a, None) is False

    def test_returns_true_when_both_are_none(self):
        assert ImageEntity.compare(None, None) is True
