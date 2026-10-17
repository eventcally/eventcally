import pytest


def test_validate_image():
    from marshmallow import ValidationError

    from project.api.image.schemas import ImageWriteRequestPlainSchema

    data = {
        "copyright_text": "Horst",
    }

    schema = ImageWriteRequestPlainSchema()

    with pytest.raises(ValidationError) as e:
        schema.load(data)

    assert "Either image_url or image_base64 has to be defined." in str(e.value)


def test_post_load_image_data(seeder):
    from project.api.image.schemas import ImageWriteRequestPlainSchema

    data = {
        "image_base64": seeder.get_default_image_upload_base64(),
        "copyright_text": "EventCally",
    }

    schema = ImageWriteRequestPlainSchema()
    result = schema.post_load_image_data(data)
    schema.load(data)

    assert result is not None


def test_load_image_data():
    from project.api.image.schemas import ImageWriteRequestPlainSchema

    schema = ImageWriteRequestPlainSchema()
    encoding_format, data = schema.load_image_data(None, None)

    assert encoding_format is None
    assert data is None
