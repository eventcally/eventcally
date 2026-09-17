from flask import request
from flask_babel import lazy_gettext
from sqlalchemy import func
from wtforms import FormField, StringField, SubmitField, TextAreaField, ValidationError
from wtforms.fields import BooleanField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms.widgets import ColorInput

from project.application.commands import (
    UpdateOrganizationCommand,
    UpdateOrganizationWidgetSettingsCommand,
)
from project.forms.common import Base64ImageForm, StrictGooglePlaceLocationForm
from project.forms.widgets import HTML5StringField
from project.models import Image, Location
from project.models.admin_unit import AdminUnit
from project.modular.base_form import BaseForm, BaseUpdateForm
from project.modular.fields import SelectMultipleTagField, VirtualFormField
from project.modular.widgets import AjaxValidationWidget
from project.utils import widget_default_background_color, widget_default_primary_color
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
        default="",
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
    admin_unit_id = (
        current_admin_unit.id
        if current_admin_unit and request.endpoint == "manage_admin_unit.update"
        else -1
    )
    organization = (
        AdminUnit.query.filter(AdminUnit.id != admin_unit_id)
        .filter(func.lower(AdminUnit.name) == name.lower())
        .first()
    )

    if organization:
        raise ValidationError(lazy_gettext("Name is already taken"))


def validate_organization_short_name(form, field):
    short_name = field.data
    admin_unit_id = (
        current_admin_unit.id
        if current_admin_unit and request.endpoint == "manage_admin_unit.update"
        else -1
    )
    organization = (
        AdminUnit.query.filter(AdminUnit.id != admin_unit_id)
        .filter(func.lower(AdminUnit.short_name) == short_name.lower())
        .first()
    )

    if organization:
        raise ValidationError(lazy_gettext("Short name is already taken"))


class AdminUnitFormMixin(object):
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
        StrictGooglePlaceLocationForm,
        default=lambda: Location(),
        label=lazy_gettext("Location"),
    )
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=lambda: Image())
    additional_information = VirtualFormField(
        AdditionalInformationForm, lazy_gettext("Additional information")
    )


class UpdateForm(BaseUpdateForm, AdminUnitFormMixin):
    verfication_requests = VirtualFormField(
        VerificationRequestsForm, lazy_gettext("Verification requests")
    )

    def create_update_command(self, admin_unit_id: int) -> UpdateOrganizationCommand:
        kwargs = dict(
            actor=self.get_current_actor(),
            id=admin_unit_id,
            name=self.name.data,
            short_name=self.short_name.data,
            description=self.description.data,
            location=self.location.form.create_update_command(),
            logo=self.logo.form.create_update_command(),
            url=self.additional_information.form.url.data,
            email=self.additional_information.form.email.data,
            phone=self.additional_information.form.phone.data,
            fax=self.additional_information.form.fax.data,
        )

        verification_requests_field = getattr(self, "verfication_requests", None)
        if verification_requests_field is not None:
            verification_requests_form = verification_requests_field.form
            kwargs["incoming_verification_requests_allowed"] = (
                verification_requests_form.incoming_verification_requests_allowed.data
            )
            kwargs["incoming_verification_requests_text"] = (
                verification_requests_form.incoming_verification_requests_text.data
            )
            kwargs["incoming_verification_requests_postal_codes"] = (
                verification_requests_form.incoming_verification_requests_postal_codes.data
            )

        return UpdateOrganizationCommand(**kwargs)


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

    def create_update_command(
        self, admin_unit_id: int
    ) -> UpdateOrganizationWidgetSettingsCommand:
        widget_background_color = self.widget_background_color.data
        if widget_background_color == widget_default_background_color:
            widget_background_color = None

        widget_primary_color = self.widget_primary_color.data
        if widget_primary_color == widget_default_primary_color:
            widget_primary_color = None

        widget_link_color = self.widget_link_color.data
        if widget_link_color == widget_default_primary_color:
            widget_link_color = None

        return UpdateOrganizationWidgetSettingsCommand(
            actor=self.get_current_actor(),
            id=admin_unit_id,
            widget_font=self.widget_font.data,
            widget_background_color=widget_background_color,
            widget_primary_color=widget_primary_color,
            widget_link_color=widget_link_color,
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
