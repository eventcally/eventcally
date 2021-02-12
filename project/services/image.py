import base64

from project.models import Image


def upsert_image_with_data(image, data, encoding_format="image/jpeg"):
    if image is None:
        image = Image()

    image.data = data
    image.encoding_format = encoding_format

    return image


def upsert_image_with_base64_str(image, base64_str, encoding_format):
    data = base64.b64decode(base64_str)
    return upsert_image_with_data(image, data, encoding_format)
