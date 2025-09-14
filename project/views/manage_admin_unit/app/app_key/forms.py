from flask_babel import lazy_gettext
from wtforms import StringField
from wtforms.validators import DataRequired

from project.modular.base_form import BaseDeleteForm


class DeleteForm(BaseDeleteForm):
    confirmation_field_name = "kid"
    kid = StringField(
        lazy_gettext("KID"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
