import os

from flask_babel import lazy_gettext
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

from project.presentation.shared.scopes import scopes
from project.presentation.web.forms.widgets import MultiCheckboxField
from project.presentation.web.modular.base_form import BaseForm


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
