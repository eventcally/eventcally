import os

from flask_babel import lazy_gettext
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from project.api import scopes
from project.forms.base_form import BaseForm
from project.forms.widgets import MultiCheckboxField
from project.utils import split_by_crlf


class BaseOAuth2ClientForm(BaseForm):
    client_name = StringField(lazy_gettext("Client name"), validators=[DataRequired()])
    redirect_uris = TextAreaField(
        lazy_gettext("Redirect URIs"), validators=[Optional()]
    )
    scope = MultiCheckboxField(
        lazy_gettext("Scopes"),
        validators=[Optional()],
        choices=[(k, k) for k, v in scopes.items()],
        render_kw={"ri": "multicheckbox"},
    )

    submit = SubmitField(lazy_gettext("Save"))

    def populate_obj(self, obj):
        meta_keys = [
            "client_name",
            "redirect_uris",
            "scope",
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


class ReadOAuth2ClientForm(BaseForm):
    client_id = StringField(lazy_gettext("Client ID"))
    client_secret = StringField(lazy_gettext("Client secret"))
    client_uri = StringField(lazy_gettext("Client URI"))
    grant_types = StringField(lazy_gettext("Grant types"))
    redirect_uris = StringField(lazy_gettext("Redirect URIs"))
    response_types = StringField(lazy_gettext("Response types"))
    scope = StringField(lazy_gettext("Scope"))
    token_endpoint_auth_method = StringField(lazy_gettext("Token endpoint auth method"))


class DeleteOAuth2ClientForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete OAuth2 client"))
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
