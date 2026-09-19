import os
from typing import Optional as OptionalType

from flask_babel import lazy_gettext
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from project.api import scopes
from project.application.commands import (
    CreateOAuth2ClientCommand,
    UpdateOAuth2ClientCommand,
)
from project.domain.types import ObjectId
from project.forms.widgets import MultiCheckboxField
from project.modular.base_form import BaseDeleteForm, BaseForm
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

    def process(self, formdata=None, obj=None, data=None, **kwargs):
        super().process(formdata, obj, data, **kwargs)

        if not obj:
            return

        formdata = self.meta.wrap_formdata(self, formdata)
        self.redirect_uris.process(formdata, os.linesep.join(obj.redirect_uris))
        self.scope.process(formdata, obj.scope.split(" "))


class CreateOAuth2ClientForm(BaseOAuth2ClientForm):
    def create_create_command(
        self,
        *,
        user_id: OptionalType[ObjectId] = None,
        admin_unit_id: OptionalType[ObjectId] = None,
    ) -> CreateOAuth2ClientCommand:
        return CreateOAuth2ClientCommand(
            actor=self.get_current_actor(),
            name=self.client_name.data,
            redirect_uris=split_by_crlf(self.redirect_uris.data),
            scope=" ".join(self.scope.data),
            user_id=user_id,
            admin_unit_id=admin_unit_id,
        )


class UpdateOAuth2ClientForm(BaseOAuth2ClientForm):
    def create_update_command(self, id: ObjectId) -> UpdateOAuth2ClientCommand:
        return UpdateOAuth2ClientCommand(
            actor=self.get_current_actor(),
            id=id,
            name=self.client_name.data,
            redirect_uris=split_by_crlf(self.redirect_uris.data),
            scope=" ".join(self.scope.data),
        )


class DeleteOAuth2ClientForm(BaseDeleteForm):
    submit = SubmitField(lazy_gettext("Delete OAuth2 client"))
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
