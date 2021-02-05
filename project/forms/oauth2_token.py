from flask_wtf import FlaskForm
from flask_babelex import lazy_gettext
from wtforms import SubmitField


class RevokeOAuth2TokenForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Revoke OAuth2 token"))
