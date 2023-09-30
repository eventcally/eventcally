from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField, FormField, StringField, SubmitField
from wtforms.fields import EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional

from project.forms.common import Base64ImageForm
from project.models import Image, Location


class OrganizerLocationForm(FlaskForm):
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


class BaseOrganizerForm(FlaskForm):
    name = StringField(
        lazy_gettext("Name"), validators=[DataRequired(), Length(max=255)]
    )
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    email = EmailField(lazy_gettext("Email"), validators=[Optional(), Length(max=255)])
    phone = TelField(lazy_gettext("Phone"), validators=[Optional(), Length(max=255)])
    fax = TelField(lazy_gettext("Fax"), validators=[Optional()])
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=lambda: Image())
    location = FormField(OrganizerLocationForm)

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:
                obj.location = Location()
            elif name == "logo" and not obj.logo:
                obj.logo = Image()
            field.populate_obj(obj, name)


class CreateOrganizerForm(BaseOrganizerForm):
    submit = SubmitField(lazy_gettext("Create organizer"))


class UpdateOrganizerForm(BaseOrganizerForm):
    submit = SubmitField(lazy_gettext("Update organizer"))


class DeleteOrganizerForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete organizer"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
