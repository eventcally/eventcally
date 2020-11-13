from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    DecimalField,
    StringField,
    SubmitField,
    TextAreaField,
    FormField,
)
from wtforms.fields.html5 import URLField
from wtforms.validators import DataRequired, Optional
from project.models import Location, Image
from project.forms.common import FileImageForm


class EventPlaceLocationForm(FlaskForm):
    street = StringField(lazy_gettext("Street"), validators=[Optional()])
    postalCode = StringField(lazy_gettext("Postal code"), validators=[Optional()])
    city = StringField(lazy_gettext("City"), validators=[Optional()])
    state = StringField(lazy_gettext("State"), validators=[Optional()])
    latitude = DecimalField(
        lazy_gettext("Latitude"), places=16, validators=[Optional()]
    )
    longitude = DecimalField(
        lazy_gettext("Longitude"), places=16, validators=[Optional()]
    )


class BaseEventPlaceForm(FlaskForm):
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
    url = URLField(lazy_gettext("Link URL"), validators=[Optional()])
    photo = FormField(FileImageForm, lazy_gettext("Photo"), default=lambda: Image())
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


class DeleteEventPlaceForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete place"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


class FindEventPlaceForm(FlaskForm):
    class Meta:
        csrf = False

    submit = SubmitField(lazy_gettext("Find places"))
