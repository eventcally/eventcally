from flask_babel import lazy_gettext
from wtforms import SubmitField

from project.modular.base_form import BaseForm


class NegotiateForm(BaseForm):
    accept = SubmitField(lazy_gettext("Accept"), render_kw={"class": "btn btn-success"})
    decline = SubmitField(
        lazy_gettext("Decline"), render_kw={"class": "btn btn-secondary"}
    )
