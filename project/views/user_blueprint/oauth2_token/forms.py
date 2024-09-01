from flask_babel import lazy_gettext
from wtforms import SubmitField

from project.forms.base_form import BaseForm


class RevokeOAuth2TokenForm(BaseForm):
    submit = SubmitField(lazy_gettext("Revoke OAuth2 token"))
