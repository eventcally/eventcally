import pytest
from sqlalchemy.exc import IntegrityError


def _owned_empty_image():
    from project.infrastructure.models import (
        AdminUnit,
        Event,
        EventOrganizer,
        EventPlace,
        Image,
    )

    image = Image(data=b"")
    admin_unit = AdminUnit(logo=image)
    event = Event()
    event.photo = image
    organizer = EventOrganizer(logo=image)
    place = EventPlace()
    place.photo = image
    return image, admin_unit, event, organizer, place


def test_fill_from_entity_and_to_entity_roundtrip(app):
    from project.domain.models.entities.image_entity import ImageEntity
    from project.infrastructure.models import Image

    entity = ImageEntity.model_construct(
        id=-1,
        hash=1,
        data=b"data",
        encoding_format="image/png",
        copyright_text="Copyright",
        license_id=None,
    )
    image = Image(id=5)

    image.fill_from_entity(entity)
    result = image.to_entity()

    assert result.id == 5
    assert result.data == b"data"
    assert result.encoding_format == "image/png"
    assert result.copyright_text == "Copyright"
    assert result.hash == 0


def test_before_flush_of_empty_image_detaches_it_from_its_owners(app, mocker):
    image, admin_unit, event, organizer, place = _owned_empty_image()
    session = mocker.Mock()

    image.before_flush(session, is_dirty=True)

    assert admin_unit.logo is None
    assert event.photo is None
    assert organizer.logo is None
    assert place.photo is None
    session.delete.assert_called_once_with(image)


def test_before_flush_of_new_empty_image_is_not_deleted(app, mocker):
    image, *_ = _owned_empty_image()
    session = mocker.Mock()

    image.before_flush(session, is_dirty=False)

    session.delete.assert_not_called()


def test_before_flush_keeps_an_image_with_data(app, mocker):
    from project.infrastructure.models import AdminUnit, Image

    image = Image(data=b"data")
    admin_unit = AdminUnit(logo=image)
    session = mocker.Mock()

    image.before_flush(session, is_dirty=True)

    assert admin_unit.logo is image
    session.delete.assert_not_called()


def test_validate_requires_copyright_text_for_images_with_data(app):
    from project.infrastructure.models import Image

    with pytest.raises(IntegrityError) as e:
        Image(data=b"data", copyright_text="  ").validate()
    assert e.value.orig.message == "Copyright text is required."

    Image(data=b"data", copyright_text="Copyright").validate()
    Image(data=b"", copyright_text=None).validate()
