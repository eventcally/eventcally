from flask_babel import lazy_gettext
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional
from wtforms.widgets import ColorInput

from project.application.commands import UpdateOrganizationWidgetSettingsCommand
from project.presentation.web.modular.base_form import BaseForm, BaseUpdateForm
from project.shared.utils import (
    widget_default_background_color,
    widget_default_primary_color,
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
