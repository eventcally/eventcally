from flask import url_for
from flask_babel import gettext, lazy_gettext
from markupsafe import Markup
from wtforms import DecimalField, StringField
from wtforms.validators import Length, Optional

from project.imageutils import (
    get_bytes_from_image,
    get_data_uri_from_bytes,
    get_image_from_base64_str,
    get_mime_type_from_image,
    resize_image_to_max,
    validate_image,
)
from project.modular.base_form import BaseForm
from project.modular.fields import GooglePlaceField


class LocationForm(BaseForm):
    street = StringField(
        lazy_gettext("Street"), validators=[Optional(), Length(max=255)]
    )
    postalCode = StringField(
        lazy_gettext("Postal code"), validators=[Optional(), Length(max=10)]
    )
    city = StringField(lazy_gettext("City"), validators=[Optional(), Length(max=255)])
    state = StringField(lazy_gettext("State"), validators=[Optional(), Length(max=255)])
    latitude = DecimalField(
        lazy_gettext("Latitude"), places=16, validators=[Optional()]
    )
    longitude = DecimalField(
        lazy_gettext("Longitude"), places=16, validators=[Optional()]
    )


class GooglePlaceLocationForm(LocationForm):
    google_place = GooglePlaceField(location_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("google_place")


class Base64ImageForm(BaseForm):
    image_base64 = StringField(
        lazy_gettext("Image"),
        render_kw={
            "data-role": "cropper-image",
            "data-min-width": 320,
            "data-min-height": 320,
        },
    )
    copyright_text = StringField(
        lazy_gettext("Copyright text"),
        validators=[Optional(), Length(max=255)],
        render_kw={"is_required": True},
    )

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        super().process(formdata, obj, data, **kwargs)

        if self.image_base64.data is None and obj and obj.data:
            self.image_base64.data = get_data_uri_from_bytes(
                obj.data, obj.encoding_format
            )

    def validate(self, extra_validators=None):
        result = super().validate(extra_validators)
        self.image_base64.encoding_format = None
        self.image_base64.image_data = None

        if self.image_base64.data:
            if not self.copyright_text.data or not self.copyright_text.data.strip():
                msg = gettext("This field is required.")
                self.copyright_text.errors.append(msg)
                result = False

            try:
                image = get_image_from_base64_str(self.image_base64.data)
                validate_image(image)
                resize_image_to_max(image)
                self.image_base64.encoding_format = get_mime_type_from_image(image)
                self.image_base64.image_data = get_bytes_from_image(image)
            except Exception as e:
                msg = str(e)
                self.image_base64.encoding_format = None
                self.image_base64.image_data = None
                self.image_base64.errors.append(msg)
                result = False

        return result

    def populate_obj(self, obj):
        super().populate_obj(obj)

        if self.image_base64.image_data and self.image_base64.encoding_format:
            obj.data = self.image_base64.image_data
            obj.encoding_format = self.image_base64.encoding_format
        else:
            obj.data = None
            obj.encoding_format = None


def get_accept_tos_markup():
    from project.services.admin import has_tos

    tos_open = '<a href="%s">' % url_for("tos")
    tos_close = "</a>"

    privacy_open = '<a href="%s">' % url_for("privacy")
    privacy_close = "</a>"

    if has_tos():
        return Markup(
            lazy_gettext(
                "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.",
                tos_open=tos_open,
                tos_close=tos_close,
                privacy_open=privacy_open,
                privacy_close=privacy_close,
            )
        )

    return Markup(
        lazy_gettext(
            "I read and accept %(privacy_open)sPrivacy%(privacy_close)s.",
            tos_open=tos_open,
            tos_close=tos_close,
            privacy_open=privacy_open,
            privacy_close=privacy_close,
        )
    )


event_rating_choices = [
    (0, lazy_gettext("0 (Little relevant)")),
    (10, "1"),
    (20, "2"),
    (30, "3"),
    (40, "4"),
    (50, lazy_gettext("5 (Default)")),
    (60, "6"),
    (70, "7"),
    (80, "8"),
    (90, "9"),
    (100, lazy_gettext("10 (Highlight)")),
]

weekday_choices = [
    (1, lazy_gettext("Monday")),
    (2, lazy_gettext("Tueday")),
    (3, lazy_gettext("Wednesday")),
    (4, lazy_gettext("Thursday")),
    (5, lazy_gettext("Friday")),
    (6, lazy_gettext("Saturday")),
    (0, lazy_gettext("Sunday")),
]

distance_choices = [
    (500, lazy_gettext("500 m")),
    (5000, lazy_gettext("5 km")),
    (10000, lazy_gettext("10 km")),
    (25000, lazy_gettext("20 km")),
    (50000, lazy_gettext("50 km")),
    (100000, lazy_gettext("100 km")),
]
