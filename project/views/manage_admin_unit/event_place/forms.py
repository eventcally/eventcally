from flask import request
from flask_babel import gettext, lazy_gettext
from sqlalchemy import func
from wtforms import FormField, StringField, SubmitField, TextAreaField
from wtforms.fields import URLField
from wtforms.validators import DataRequired, Length, Optional

from project.forms.common import Base64ImageForm, LocationForm
from project.models import Image, Location
from project.models.event_place import EventPlace
from project.modular.base_form import BaseForm, BaseListForm
from project.modular.fields import GooglePlaceField
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.modular.widgets import AjaxValidationWidget
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
    photo = FormField(Base64ImageForm, lazy_gettext("Photo"), default=lambda: Image())
    url = URLField(lazy_gettext("Link URL"), validators=[Optional(), Length(max=255)])
    description = TextAreaField(lazy_gettext("Description"), validators=[Optional()])

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:
                obj.location = Location()
            elif name == "photo" and not obj.photo:
                obj.photo = Image()
            field.populate_obj(obj, name)

    def ajax_validate_name(self, object, field, **kwargs):
        name = request.form["name"]
        admin_unit_id = current_admin_unit.id
        event_place_id = object.id if object else -1
        event_place = (
            EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)
            .filter(EventPlace.id != event_place_id)
            .filter(func.lower(EventPlace.name) == name.lower())
            .first()
        )

        if event_place:
            return gettext("A place already exists with this name.")

        return True


class CreateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Create place"))


class UpdateEventPlaceForm(BaseEventPlaceForm):
    submit = SubmitField(lazy_gettext("Update place"))


class DeleteEventPlaceForm(BaseForm):
    submit = SubmitField(lazy_gettext("Delete place"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


class ListForm(BaseListForm):
    sort_definitions = [
        SortDefinition(EventPlace.name, func=func.lower, label=lazy_gettext("Name")),
        SortDefinition(
            EventPlace.last_modified_at,
            desc=True,
            label=lazy_gettext("Last modified first"),
        ),
        SortDefinition(
            EventPlace.number_of_events,
            desc=True,
            label=lazy_gettext("Number of events"),
        ),
    ]
    search_definitions = [SearchDefinition(EventPlace.name)]

    # def apply_query_filter(self, query, **kwargs):
    #     query = super().apply_query_filter(query, **kwargs)
    #     if not self.keyword.data:
    #         return query

    #     stmt = parse_like_term(self.keyword.data)

    #     filter_stmt = []
    #     filter_stmt.append(EventPlace.name.ilike(stmt))

    #     location_alias = aliased(Location)
    #     query = query.outerjoin(location_alias)
    #     filter_stmt.append(location_alias.postalCode.ilike(stmt))
    #     filter_stmt.append(location_alias.street.ilike(stmt))
    #     filter_stmt.append(location_alias.city.ilike(stmt))
    #     filter_stmt.append(location_alias.state.ilike(stmt))

    #     query = query.filter(or_(*filter_stmt))
    #     return query
