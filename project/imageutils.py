import base64
import re
from io import BytesIO

import PIL
import requests

min_image_size = 320
max_image_size = 1024
supported_formats = ["jpeg", "png", "gif"]


def get_data_uri_from_bytes(data: bytes, encoding_format: str) -> str:
    base64_str = base64.b64encode(data).decode("utf-8")
    return "data:{};base64,{}".format(encoding_format, base64_str)


def get_image_from_bytes(data: bytes) -> PIL.Image:
    return PIL.Image.open(BytesIO(data))


def get_image_from_base64_str(base64_str: str) -> PIL.Image:
    image_data = re.sub("^data:image/.+;base64,", "", base64_str)
    return get_image_from_bytes(base64.b64decode(image_data))


def get_image_from_url(url: str) -> PIL.Image:
    response = requests.get(url)
    return get_image_from_bytes(response.content)


def get_mime_type_from_image(image: PIL.Image) -> str:
    return image.get_format_mimetype()


def get_bytes_from_image(image: PIL.Image) -> bytes:
    imgByteArr = BytesIO()
    image.save(imgByteArr, format=image.format)
    return imgByteArr.getvalue()


def resize_image_to_max(image: PIL.Image):
    if image.width > max_image_size or image.height > max_image_size:
        image.thumbnail((max_image_size, max_image_size), PIL.Image.ANTIALIAS)


def validate_image(image: PIL.Image):
    if image.width < min_image_size or image.height < min_image_size:
        raise ValueError(
            f"Image is too small ({image.width}x{image.height}px). At least {min_image_size}x{min_image_size}px."
        )

    if image.format.lower() not in supported_formats:
        raise ValueError(
            f"Image format {image.format} is not supported. Supported formats: {', '.join(supported_formats)}."
        )
