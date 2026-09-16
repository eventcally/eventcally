from typing import Optional

from flask_babel import lazy_gettext
from wtforms import StringField
from wtforms.validators import DataRequired

from project.application.commands import CreateApiKeyCommand, UpdateApiKeyCommand
from project.domain.types import ObjectId
from project.modular.base_form import BaseCreateForm, BaseDeleteForm, BaseUpdateForm


class CreateForm(BaseCreateForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )

    def create_create_command(
        self,
        *,
        user_id: Optional[ObjectId] = None,
        admin_unit_id: Optional[ObjectId] = None,
    ) -> CreateApiKeyCommand:
        return CreateApiKeyCommand(
            actor=self.get_current_actor(),
            name=self.name.data,
            user_id=user_id,
            admin_unit_id=admin_unit_id,
        )


class UpdateForm(BaseUpdateForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )

    def create_update_command(self, id: ObjectId) -> UpdateApiKeyCommand:
        return UpdateApiKeyCommand(
            actor=self.get_current_actor(),
            id=id,
            name=self.name.data,
        )


class DeleteForm(BaseDeleteForm):
    confirmation_field_name = "name"
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired()],
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
