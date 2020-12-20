from flask import url_for
from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import Optional
from markupsafe import Markup
import re
import base64


class BaseImageForm(FlaskForm):
    copyright_text = StringField(
        lazy_gettext("Copyright text"), validators=[Optional()]
    )


class FileImageForm(BaseImageForm):
    image_file = FileField(
        lazy_gettext("File"),
        validators=[FileAllowed(["jpg", "jpeg", "png"], lazy_gettext("Images only!"))],
    )
    delete_flag = BooleanField(
        lazy_gettext("Delete image"), default=False, validators=[Optional()]
    )

    def populate_obj(self, obj):
        super(BaseImageForm, self).populate_obj(obj)

        if self.image_file.data:
            fs = self.image_file.data
            obj.data = fs.read()
            obj.encoding_format = fs.content_type
        elif self.delete_flag.data:
            obj.data = None
            obj.encoding_format = None


class Base64ImageForm(BaseImageForm):
    image_base64 = HiddenField()

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        super(BaseImageForm, self).process(formdata, obj, data, **kwargs)

        if self.image_base64.data is None and obj and obj.data:
            base64_str = base64.b64encode(obj.data).decode("utf-8")
            self.image_base64.data = "data:{};base64,{}".format(
                obj.encoding_format, base64_str
            )

    def populate_obj(self, obj):
        super(BaseImageForm, self).populate_obj(obj)

        match = None
        if self.image_base64.data:
            match = re.match(r"^data:(image/.+);base64,(.*)$", self.image_base64.data)

        if match:
            obj.encoding_format = match.group(1)
            base64_str = match.group(2)
            obj.data = base64.b64decode(base64_str)
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
    (50, "5"),
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
