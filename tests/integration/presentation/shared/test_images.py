import base64
import io

import pytest
from PIL import Image

from project.presentation.shared.images import image_value_object_from_data_uri


def _data_uri(size):
    buffer = io.BytesIO()
    Image.new("RGB", size, (10, 120, 200)).save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def test_valid_image():
    image = image_value_object_from_data_uri(_data_uri((400, 400)), "Me", 4)

    assert image.encoding_format == "image/png"
    assert image.copyright_text == "Me"
    assert image.license_id == 4
    assert image.data


def test_too_small():
    with pytest.raises(ValueError, match="too small"):
        image_value_object_from_data_uri(_data_uri((100, 100)), None, None)


def test_garbage():
    with pytest.raises(Exception):
        image_value_object_from_data_uri("data:image/png;base64,AAAA", None, None)
