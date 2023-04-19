from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SubmitField


class RevokeOAuth2TokenForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Revoke OAuth2 token"))
