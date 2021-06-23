import pytest


def test_validate_image():
    from marshmallow import ValidationError

    from project.api.image.schemas import ImagePostRequestSchema

    data = {
        "copyright_text": "Horst",
    }

    schema = ImagePostRequestSchema()

    with pytest.raises(ValidationError) as e:
        schema.load(data)

    assert "Either image_url or image_base64 has to be defined." in str(e.value)


def test_post_load_image_data(seeder):
    from project.api.image.schemas import ImagePostRequestSchema

    data = {
        "image_base64": seeder.get_default_image_upload_base64(),
    }

    item = dict()
    schema = ImagePostRequestSchema()
    schema.post_load_image_data(item, data)
    schema.load(data)

    assert item.get("encoding_format") is not None
    assert item.get("data") is not None


def test_load_image_data():
    from project.api.image.schemas import ImagePostRequestSchema

    schema = ImagePostRequestSchema()
    encoding_format, data = schema.load_image_data(None, None)

    assert encoding_format is None
    assert data is None
