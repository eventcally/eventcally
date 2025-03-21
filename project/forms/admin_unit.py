from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import (
    DecimalField,
    FormField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.fields import BooleanField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp

from project.forms.common import Base64ImageForm
from project.forms.widgets import HTML5StringField
from project.models import AdminUnitRelation, Image, Location


class AdminUnitLocationForm(FlaskForm):
    street = StringField(
        lazy_gettext("Street"), validators=[Optional(), Length(max=255)]
    )
    postalCode = StringField(
        lazy_gettext("Postal code"), validators=[DataRequired(), Length(max=10)]
    )
    city = StringField(
        lazy_gettext("City"), validators=[DataRequired(), Length(max=255)]
    )
    state = StringField(lazy_gettext("State"), validators=[Optional(), Length(max=255)])
    latitude = DecimalField(
        lazy_gettext("Latitude"), places=16, validators=[Optional()]
    )
    longitude = DecimalField(
        lazy_gettext("Longitude"), places=16, validators=[Optional()]
    )


class BaseAdminUnitForm(FlaskForm):
    name = HTML5StringField(
        lazy_gettext("Name of organization"),
        description=lazy_gettext("The full name of the organization"),
        validators=[DataRequired(), Length(min=5, max=255)],
    )
    short_name = HTML5StringField(
        lazy_gettext("Short name for organization"),
        description=lazy_gettext(
            "The short name is used to create a unique identifier for your events"
        ),
        validators=[
            DataRequired(),
            Length(min=5, max=100),
            Regexp(
                r"^\w+$",
                message=lazy_gettext(
                    "Short name must contain only letters numbers or underscore"
                ),
            ),
        ],
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        description=lazy_gettext("Describe the organization in a few words"),
        validators=[Optional()],
    )
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    email = EmailField(lazy_gettext("Email"), validators=[Optional(), Length(max=255)])
    phone = TelField(lazy_gettext("Phone"), validators=[Optional(), Length(max=255)])
    fax = TelField(lazy_gettext("Fax"), validators=[Optional(), Length(max=255)])
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=lambda: Image())
    location = FormField(AdminUnitLocationForm, default=lambda: Location())

    incoming_verification_requests_allowed = BooleanField(
        lazy_gettext("Allow verification requests"),
        description=lazy_gettext(
            "If set, unverified organizations may ask you for verification."
        ),
        validators=[Optional()],
    )
    incoming_verification_requests_text = TextAreaField(
        lazy_gettext("Verification requests information"),
        validators=[Optional()],
        default=[],
        description=lazy_gettext(
            "This text is shown to unverified organizations to help them decide whether they ask you for verification."
        ),
    )
    incoming_verification_requests_postal_codes = SelectMultipleField(
        lazy_gettext("Verification requests postal codes"),
        validators=[Optional()],
        validate_choice=False,
        choices=[],
        description=lazy_gettext(
            "Limit verification requests to organizations with these postal codes."
        ),
    )

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:  # pragma: no cover
                obj.location = Location()
            elif name == "logo" and not obj.logo:
                obj.logo = Image()
            field.populate_obj(obj, name)


class AdminUnitRelationForm(FlaskForm):
    verify = BooleanField(
        lazy_gettext("Verify new organization"),
        description=lazy_gettext(
            "If set, events of the new organization are publicly visible."
        ),
        validators=[Optional()],
    )
    auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the new organization are verified automatically."
        ),
        validators=[Optional()],
    )


class CreateAdminUnitForm(BaseAdminUnitForm):
    embedded_relation = FormField(
        AdminUnitRelationForm, default=lambda: AdminUnitRelation()
    )
    submit = SubmitField(lazy_gettext("Create organization"))

    def populate_obj(self, obj):
        super().populate_obj(obj)
        delattr(obj, "embedded_relation")


class UpdateAdminUnitForm(BaseAdminUnitForm):
    submit = SubmitField(lazy_gettext("Update settings"))
