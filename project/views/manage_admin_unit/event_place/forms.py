from flask import request
from flask_babel import gettext, lazy_gettext
from wtforms import FormField, StringField, SubmitField, TextAreaField
from wtforms.fields import URLField
from wtforms.validators import DataRequired, Length, Optional

from project.application.commands import (
    CreateEventPlaceCommand,
    UpdateEventPlaceCommand,
)
from project.application.queries import IsEventPlaceNameTakenQuery
from project.forms.common import Base64ImageForm, LocationForm
from project.views.modular.base_form import BaseForm
from project.views.modular.fields import GooglePlaceField
from project.views.modular.widgets import AjaxValidationWidget
from project.views.utils import current_admin_unit


class BaseEventPlaceForm(BaseForm):
    google_place = GooglePlaceField()
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired(), Length(max=255)],
        widget=AjaxValidationWidget(),
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
    location = FormField(LocationForm, lazy_gettext("Location"))
    photo = FormField(Base64ImageForm, lazy_gettext("Photo"))
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    description = TextAreaField(lazy_gettext("Description"), validators=[Optional()])

    def ajax_validate_name(self, object, field, **kwargs):
        query = IsEventPlaceNameTakenQuery(
            admin_unit_id=current_admin_unit.id,
            name=request.form["name"],
            exclude_id=object.id if object else None,
        )

        if self.get_query_bus().handle(query):
            return gettext("A place already exists with this name.")

        return True


class CreateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Create place"))

    def create_create_command(self, admin_unit_id: int) -> CreateEventPlaceCommand:
        return CreateEventPlaceCommand(
            actor=self.get_current_actor(),
            admin_unit_id=admin_unit_id,
            name=self.name.data,
            url=self.url.data,
            description=self.description.data,
            location=self.location.form.create_create_command(),
            photo=self.photo.form.create_create_command(),
        )


class UpdateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Update place"))

    def create_update_command(self, event_place_id: int) -> UpdateEventPlaceCommand:
        return UpdateEventPlaceCommand(
            actor=self.get_current_actor(),
            id=event_place_id,
            name=self.name.data,
            url=self.url.data,
            description=self.description.data,
            location=self.location.form.create_update_command(),
            photo=self.photo.form.create_update_command(),
        )


class DeleteEventPlaceForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete place"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
