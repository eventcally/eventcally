from flask_babel import lazy_gettext
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from project.modular.base_form import BaseDeleteForm


class DeleteForm(BaseDeleteForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
    submit = SubmitField(
        lazy_gettext("Leave organization"), render_kw={"class": "btn btn-danger"}
    )
