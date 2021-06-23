from flask import url_for
from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import HiddenField, StringField
from wtforms.validators import Optional

from project.imageutils import (
    get_bytes_from_image,
    get_data_uri_from_bytes,
    get_image_from_base64_str,
    get_mime_type_from_image,
    resize_image_to_max,
    validate_image,
)


class BaseImageForm(FlaskForm):
    copyright_text = StringField(
        lazy_gettext("Copyright text"), validators=[Optional()]
    )


class Base64ImageForm(BaseImageForm):
    image_base64 = HiddenField()

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        super(BaseImageForm, self).process(formdata, obj, data, **kwargs)

        if self.image_base64.data is None and obj and obj.data:
            self.image_base64.data = get_data_uri_from_bytes(
                obj.data, obj.encoding_format
            )

    def populate_obj(self, obj):
        super(BaseImageForm, self).populate_obj(obj)

        if self.image_base64.data:
            image = get_image_from_base64_str(self.image_base64.data)
            validate_image(image)
            resize_image_to_max(image)
            obj.encoding_format = get_mime_type_from_image(image)
            obj.data = get_bytes_from_image(image)
        else:
            obj.data = None
            obj.encoding_format = None


def get_accept_tos_markup():
    tos_open = '<a href="%s">' % url_for("tos")
    tos_close = "</a>"

    privacy_open = '<a href="%s">' % url_for("privacy")
    privacy_close = "</a>"

    return Markup(
        lazy_gettext(
            "I read and accept %(tos_open)sTerms of Service%(tos_close)s and %(privacy_open)sPrivacy%(privacy_close)s.",
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
