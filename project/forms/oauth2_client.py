import os

from flask_babelex import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from project.api import scopes
from project.forms.widgets import MultiCheckboxField
from project.utils import split_by_crlf


class BaseOAuth2ClientForm(FlaskForm):
    client_name = StringField(lazy_gettext("Client name"), validators=[DataRequired()])
    redirect_uris = TextAreaField(
        lazy_gettext("Redirect URIs"), validators=[Optional()]
    )
    grant_types = MultiCheckboxField(
        lazy_gettext("Grant types"),
        validators=[DataRequired()],
        choices=[
            ("authorization_code", lazy_gettext("Authorization Code")),
            ("refresh_token", lazy_gettext("Refresh Token")),
        ],
        default=["authorization_code", "refresh_token"],
    )
    response_types = MultiCheckboxField(
        lazy_gettext("Response types"),
        validators=[DataRequired()],
        choices=[
            ("code", "code"),
        ],
        default=["code"],
    )
    scope = MultiCheckboxField(
        lazy_gettext("Scopes"),
        validators=[DataRequired()],
        choices=[(k, k) for k, v in scopes.items()],
    )
    token_endpoint_auth_method = SelectField(
        lazy_gettext("Token endpoint auth method"),
        validators=[DataRequired()],
        choices=[
            ("client_secret_post", lazy_gettext("Client secret post")),
            ("client_secret_basic", lazy_gettext("Client secret basic")),
        ],
    )

    submit = SubmitField(lazy_gettext("Save"))

    def populate_obj(self, obj):
        meta_keys = [
            "client_name",
            "client_uri",
            "grant_types",
            "redirect_uris",
            "response_types",
            "scope",
            "token_endpoint_auth_method",
        ]
        metadata = dict()
        for name, field in self._fields.items():
            if name in meta_keys:
                if name == "redirect_uris":
                    metadata[name] = split_by_crlf(field.data)
                elif name == "scope":
                    metadata[name] = " ".join(field.data)
                else:
                    metadata[name] = field.data
            else:
                field.populate_obj(obj, name)
        obj.set_client_metadata(metadata)

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        super().process(formdata, obj, data, **kwargs)

        if not obj:
            return

        formdata = self.meta.wrap_formdata(self, formdata)
        self.redirect_uris.process(formdata, os.linesep.join(obj.redirect_uris))
        self.scope.process(formdata, obj.scope.split(" "))


class CreateOAuth2ClientForm(BaseOAuth2ClientForm):
    pass


class UpdateOAuth2ClientForm(BaseOAuth2ClientForm):
    pass


class DeleteOAuth2ClientForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete OAuth2 client"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
