from flask_babel import lazy_gettext
from wtforms import DecimalField, FormField, StringField, SubmitField, TextAreaField
from wtforms.fields import URLField
from wtforms.validators import DataRequired, Length, Optional

from project.forms.common import Base64ImageForm
from project.models import Image, Location
from project.modular.base_form import BaseForm


class EventPlaceLocationForm(BaseForm):
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


class BaseEventPlaceForm(BaseForm):
    name = StringField(
        lazy_gettext("Name"), validators=[DataRequired(), Length(max=255)]
    )
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    photo = FormField(Base64ImageForm, lazy_gettext("Photo"), default=lambda: Image())
    description = TextAreaField(lazy_gettext("Description"), validators=[Optional()])
    location = FormField(EventPlaceLocationForm)

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:
                obj.location = Location()
            elif name == "photo" and not obj.photo:
                obj.photo = Image()
            field.populate_obj(obj, name)


class CreateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Create place"))


class UpdateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Update place"))


class DeleteEventPlaceForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete place"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
