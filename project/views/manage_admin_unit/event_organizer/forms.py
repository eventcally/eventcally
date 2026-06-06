from flask import request
from flask_babel import gettext, lazy_gettext
from sqlalchemy import func
from wtforms import FormField, StringField, SubmitField
from wtforms.fields import EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional

from project.application.commands import (
    CreateEventOrganizerCommand,
    UpdateEventOrganizerCommand,
)
from project.forms.common import Base64ImageForm, GooglePlaceLocationForm
from project.models import Image
from project.models.event_organizer import EventOrganizer
from project.modular.base_form import BaseForm
from project.modular.widgets import AjaxValidationWidget
from project.views.utils import current_admin_unit


class BaseEventOrganizerForm(BaseForm):
    name = StringField(
        lazy_gettext("Name"),
        validators=[DataRequired(), Length(max=255)],
        widget=AjaxValidationWidget(),
        render_kw={"role": "presentation", "autocomplete": "off"},
    )
    location = FormField(GooglePlaceLocationForm, lazy_gettext("Location"))
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=lambda: Image())
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    email = EmailField(lazy_gettext("Email"), validators=[Optional(), Length(max=255)])
    phone = TelField(lazy_gettext("Phone"), validators=[Optional(), Length(max=255)])
    fax = TelField(lazy_gettext("Fax"), validators=[Optional()])

    def ajax_validate_name(self, object, field, **kwargs):
        name = request.form["name"]
        admin_unit_id = current_admin_unit.id
        event_organizer_id = object.id if object else -1
        event_organizer = (
            EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit_id)
            .filter(EventOrganizer.id != event_organizer_id)
            .filter(func.lower(EventOrganizer.name) == name.lower())
            .first()
        )

        if event_organizer:
            return gettext("An organizer already exists with this name.")

        return True


class CreateEventOrganizerForm(BaseEventOrganizerForm):
    submit = SubmitField(lazy_gettext("Create organizer"))

    def create_create_command(self, admin_unit_id: int) -> CreateEventOrganizerCommand:
        return CreateEventOrganizerCommand.model_construct(
            admin_unit_id=admin_unit_id,
            name=self.name.data,
            url=self.url.data,
            email=self.email.data,
            phone=self.phone.data,
            fax=self.fax.data,
            location=self.location.form.create_create_command(),
            logo=self.logo.form.create_create_command(),
        )


class UpdateEventOrganizerForm(BaseEventOrganizerForm):
    submit = SubmitField(lazy_gettext("Update organizer"))

    def create_update_command(
        self, event_organizer_id: int
    ) -> UpdateEventOrganizerCommand:
        return UpdateEventOrganizerCommand.model_construct(
            id=event_organizer_id,
            name=self.name.data,
            url=self.url.data,
            email=self.email.data,
            phone=self.phone.data,
            fax=self.fax.data,
            location=self.location.form.create_update_command(),
            logo=self.logo.form.create_update_command(),
        )


class DeleteEventOrganizerForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete organizer"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
