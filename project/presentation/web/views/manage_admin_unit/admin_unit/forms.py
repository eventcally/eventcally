from flask import current_app
from flask_babel import lazy_gettext
from wtforms import FormField, StringField, SubmitField, TextAreaField, ValidationError
from wtforms.fields import EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms.widgets import ColorInput

from project.application.commands import UpdateOrganizationWidgetSettingsCommand
from project.application.queries import (
    IsOrganizationNameTakenQuery,
    IsOrganizationShortNameTakenQuery,
)
from project.presentation.web.forms.common import (
    Base64ImageForm,
    StrictGooglePlaceLocationForm,
)
from project.presentation.web.forms.widgets import HTML5StringField
from project.presentation.web.modular.base_form import (
    BaseForm,
    BaseUpdateForm,
    BlankFormData,
)
from project.presentation.web.modular.fields import VirtualFormField
from project.presentation.web.modular.widgets import AjaxValidationWidget
from project.shared.utils import (
    widget_default_background_color,
    widget_default_primary_color,
)


class AdditionalInformationForm(BaseForm):
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    email = EmailField(lazy_gettext("Email"), validators=[Optional(), Length(max=255)])
    phone = TelField(lazy_gettext("Phone"), validators=[Optional(), Length(max=255)])
    fax = TelField(lazy_gettext("Fax"), validators=[Optional(), Length(max=255)])


def _query_bus():
    return current_app.container.cqrs.query_bus()


def validate_organization_name(form, field):
    name = field.data
    if _query_bus().handle(IsOrganizationNameTakenQuery(name=name)):
        raise ValidationError(lazy_gettext("Name is already taken"))


def validate_organization_short_name(form, field):
    short_name = field.data
    if _query_bus().handle(IsOrganizationShortNameTakenQuery(short_name=short_name)):
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
        default=BlankFormData,
        label=lazy_gettext("Location"),
    )
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=BlankFormData)
    additional_information = VirtualFormField(
        AdditionalInformationForm, lazy_gettext("Additional information")
    )


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
