from flask_babel import lazy_gettext
from wtforms import BooleanField, EmailField, StringField
from wtforms.validators import DataRequired, Length

from project.modular.base_form import BaseCreateForm, BaseUpdateForm


class SharedFormMixin(object):
    admin_unit_name = StringField(
        lazy_gettext("New organization's name"),
        validators=[DataRequired(), Length(max=255)],
    )
    relation_verify = BooleanField(
        lazy_gettext("Verify new organization"),
        description=lazy_gettext(
            "If set, events of the new organization are publicly visible."
        ),
        render_kw={"ri": "switch"},
    )
    relation_auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the new organization are verified automatically."
        ),
        render_kw={"ri": "switch"},
    )


class CreateForm(BaseCreateForm, SharedFormMixin):
    email = EmailField(
        lazy_gettext("Email"),
        description=lazy_gettext("The invitation will be sent to this email address."),
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("email")


class UpdateForm(BaseUpdateForm, SharedFormMixin):
    pass
