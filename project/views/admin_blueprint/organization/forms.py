from flask_babel import lazy_gettext
from wtforms import BooleanField, StringField
from wtforms.validators import DataRequired, Optional

from project.modular.base_form import BaseDeleteForm, BaseUpdateForm


class UpdateForm(BaseUpdateForm):
    incoming_reference_requests_allowed = BooleanField(
        lazy_gettext("Incoming reference requests allowed"),
        description=lazy_gettext(
            "If set, other organizations can ask this organization to reference their event."
        ),
        validators=[Optional()],
        render_kw={"ri": "switch"},
    )
    can_create_other = BooleanField(
        lazy_gettext("Create other organizations"),
        description=lazy_gettext(
            "If set, members of the organization can create other organizations."
        ),
        validators=[Optional()],
        render_kw={"ri": "switch"},
    )
    can_invite_other = BooleanField(
        lazy_gettext("Invite other organizations"),
        description=lazy_gettext(
            "If set, members of the organization can invite other organizations."
        ),
        validators=[Optional()],
        render_kw={"ri": "switch"},
    )
    can_verify_other = BooleanField(
        lazy_gettext("Verify other organizations"),
        description=lazy_gettext(
            "If set, members of the organization can verify other organizations."
        ),
        validators=[Optional()],
        render_kw={"ri": "switch"},
    )


class DeleteForm(BaseDeleteForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
