import os

from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from project.api import scopes
from project.forms.widgets import MultiCheckboxField
from project.utils import split_by_crlf


class BaseOAuth2ClientForm(FlaskForm):
    client_name = StringField(lazy_gettext("Client name"), validators=[DataRequired()])
    redirect_uris = TextAreaField(
        lazy_gettext("Redirect URIs"), validators=[Optional()]
    )
    scope = MultiCheckboxField(
        lazy_gettext("Scopes"),
        validators=[Optional()],
        choices=[(k, k) for k, v in scopes.items()],
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


class DeleteOAuth2ClientForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Delete OAuth2 client"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
