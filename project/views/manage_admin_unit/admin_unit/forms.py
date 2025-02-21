from flask_babel import lazy_gettext
from sqlalchemy import func
from wtforms import FormField, StringField, SubmitField, TextAreaField, ValidationError
from wtforms.fields import BooleanField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms.widgets import ColorInput

from project.forms.common import Base64ImageForm, GooglePlaceLocationForm
from project.forms.widgets import HTML5StringField
from project.models import Image, Location
from project.models.admin_unit import AdminUnit
from project.modular.base_form import BaseForm, BaseUpdateForm
from project.modular.fields import SelectMultipleTagField, VirtualFormField
from project.modular.widgets import AjaxValidationWidget
from project.views.utils import current_admin_unit


class AdditionalInformationForm(BaseForm):
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    email = EmailField(lazy_gettext("Email"), validators=[Optional(), Length(max=255)])
    phone = TelField(lazy_gettext("Phone"), validators=[Optional(), Length(max=255)])
    fax = TelField(lazy_gettext("Fax"), validators=[Optional(), Length(max=255)])


class VerificationRequestsForm(BaseForm):
    incoming_verification_requests_allowed = BooleanField(
        lazy_gettext("Allow verification requests"),
        description=lazy_gettext(
            "If set, unverified organizations may ask you for verification."
        ),
        validators=[Optional()],
        render_kw={"ri": "checkbox"},
    )
    incoming_verification_requests_text = TextAreaField(
        lazy_gettext("Verification requests information"),
        validators=[Optional()],
        default=[],
        description=lazy_gettext(
            "This text is shown to unverified organizations to help them decide whether they ask you for verification."
        ),
    )
    incoming_verification_requests_postal_codes = SelectMultipleTagField(
        lazy_gettext("Verification requests postal codes"),
        validators=[Optional()],
        description=lazy_gettext(
            "Limit verification requests to organizations with these postal codes."
        ),
    )


def validate_organization_name(form, field):
    name = field.data
    admin_unit_id = current_admin_unit.id
    organization = (
        AdminUnit.query.filter(AdminUnit.id != admin_unit_id)
        .filter(func.lower(AdminUnit.name) == name.lower())
        .first()
    )

    if organization:
        raise ValidationError(lazy_gettext("Name is already taken"))


def validate_organization_short_name(form, field):
    short_name = field.data
    admin_unit_id = current_admin_unit.id
    organization = (
        AdminUnit.query.filter(AdminUnit.id != admin_unit_id)
        .filter(func.lower(AdminUnit.short_name) == short_name.lower())
        .first()
    )

    if organization:
        raise ValidationError(lazy_gettext("Short name is already taken"))


class UpdateForm(BaseUpdateForm):
    name = HTML5StringField(
        lazy_gettext("Name of organization"),
        description=lazy_gettext("The full name of the organization"),
        validators=[DataRequired(), Length(min=5, max=255), validate_organization_name],
        widget=AjaxValidationWidget(),
        render_kw={
            "role": "presentation",
            "autocomplete": "off",
        },
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
            validate_organization_short_name,
        ],
        widget=AjaxValidationWidget(),
        render_kw={
            "role": "presentation",
            "autocomplete": "off",
        },
    )
    description = TextAreaField(
        lazy_gettext("Description"),
        description=lazy_gettext("Describe the organization in a few words"),
        validators=[Optional()],
    )
    location = FormField(
        GooglePlaceLocationForm,
        default=lambda: Location(),
        label=lazy_gettext("Location"),
    )
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=lambda: Image())
    additional_information = VirtualFormField(
        AdditionalInformationForm, lazy_gettext("Additional information")
    )
    verfication_requests = VirtualFormField(
        VerificationRequestsForm, lazy_gettext("Verification requests")
    )

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:  # pragma: no cover
                obj.location = Location()
            elif name == "logo" and not obj.logo:
                obj.logo = Image()
            field.populate_obj(obj, name)


class UpdateWidgetForm(BaseUpdateForm):
    widget_font = StringField(
        lazy_gettext("Font"), validators=[Optional(), Length(max=255)]
    )
    widget_background_color = StringField(
        lazy_gettext("Background Color"),
        default="#ffffff",
        widget=ColorInput(),
        validators=[Optional()],
    )
    widget_primary_color = StringField(
        lazy_gettext("Primary Color"),
        default="#007bff",
        widget=ColorInput(),
        validators=[Optional()],
    )
    widget_link_color = StringField(
        lazy_gettext("Link Color"),
        default="#007bff",
        widget=ColorInput(),
        validators=[Optional()],
    )


class RequestDeletionForm(BaseForm):
    name = StringField(
        lazy_gettext("Name of organization"),
        validators=[DataRequired()],
        render_kw={
            "role": "presentation",
            "autocomplete": "off",
        },
    )
    submit = SubmitField(lazy_gettext("Request deletion"))


class CancelDeletionForm(RequestDeletionForm):
    submit = SubmitField(lazy_gettext("Cancel deletion"))
