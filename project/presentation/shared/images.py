from typing import Optional

from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.shared.imageutils import (
    get_bytes_from_image,
    get_image_from_base64_str,
    get_mime_type_from_image,
    resize_image_to_max,
    validate_image,
)


def image_value_object_from_data_uri(
    data_uri: str, copyright_text: Optional[str], license_id: Optional[int]
) -> ImageValueObject:
    """Decodes, validates and downsizes an uploaded data URI.

    Raises `ValueError` (the `validate_image` message) for unusable images.
    """
    image = get_image_from_base64_str(data_uri)
    validate_image(image)
    resize_image_to_max(image)
    return ImageValueObject(
        data=get_bytes_from_image(image),
        encoding_format=get_mime_type_from_image(image),
        copyright_text=copyright_text,
        license_id=license_id,
    )
