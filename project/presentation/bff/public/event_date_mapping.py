import re
from html import unescape

from project.presentation.bff.public.schemas import WidgetPhoto
from project.presentation.shared.urls import url_for_image

DESCRIPTION_PREVIEW_LENGTH = 200
_TAG = re.compile(r"<[^>]*>")
_WHITESPACE = re.compile(r"\s+")


def description_preview(html, length: int = DESCRIPTION_PREVIEW_LENGTH):
    """Plain text of a stored HTML description, cut at a word boundary."""
    if not html:
        return None

    text = _WHITESPACE.sub(" ", unescape(_TAG.sub(" ", html))).strip()

    if not text:
        return None

    if len(text) <= length:
        return text

    cut = text[: length - 1]
    boundary = cut.rfind(" ")
    return (cut[:boundary] if boundary > 0 else cut) + "…"


def photo_of(image):
    if not image:
        return None

    return WidgetPhoto(
        url_200=url_for_image(image, s=200),
        url_500=url_for_image(image, s=500),
        copyright_text=image.copyright_text,
        license_code=image.license.code if image.license else None,
        license_url=image.license.url if image.license else None,
    )
