from typing import Optional

from flask_babel import gettext

from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.presentation.bff.manage.schemas import OrganizationLogo
from project.presentation.shared.images import image_value_object_from_data_uri
from project.shared.imageutils import get_data_uri_from_bytes


def image_from_save(
    image: Optional[OrganizationLogo], stored_image, errors: list, loc: list[str]
):
    """The image field of a save body. `image_base64=None` keeps `stored_image` (none
    when creating). Errors are appended with the path `loc` of the field."""
    if image is None:
        return None

    result = None

    if image.image_base64 is None:
        if stored_image and stored_image.data:
            result = ImageValueObject(
                data=stored_image.data,
                encoding_format=stored_image.encoding_format,
                copyright_text=image.copyright_text,
                license_id=image.license_id,
            )
    else:
        try:
            result = image_value_object_from_data_uri(
                image.image_base64, image.copyright_text, image.license_id
            )
        except Exception as e:
            errors.append(([*loc, "image_base64"], str(e)))

    if result is not None and not (image.copyright_text or "").strip():
        errors.append(([*loc, "copyright_text"], gettext("This field is required.")))

    return result


def image_form_value(image) -> Optional[OrganizationLogo]:
    """The image field of a form from the stored image's read model (`None` when the
    image is empty). The data stays a data URI the form can preview."""
    if not (image and image.data):
        return None

    return OrganizationLogo(
        image_base64=get_data_uri_from_bytes(image.data, image.encoding_format),
        copyright_text=image.copyright_text,
        license_id=image.license.id if image.license else None,
    )
