from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import DecimalField, FormField, StringField, SubmitField, TextAreaField
from wtforms.fields import BooleanField, EmailField, TelField, URLField
from wtforms.validators import DataRequired, Length, Optional, Regexp
from wtforms.widgets import ColorInput

from project.forms.common import Base64ImageForm
from project.forms.widgets import HTML5StringField
from project.models import AdminUnitRelation, Image, Location


class AdminUnitLocationForm(FlaskForm):
    street = StringField(lazy_gettext("Street"), validators=[Optional()])
    postalCode = StringField(lazy_gettext("Postal code"), validators=[DataRequired()])
    city = StringField(lazy_gettext("City"), validators=[DataRequired()])
    state = StringField(lazy_gettext("State"), validators=[Optional()])
    latitude = DecimalField(
        lazy_gettext("Latitude"), places=16, validators=[Optional()]
    )
    longitude = DecimalField(
        lazy_gettext("Longitude"), places=16, validators=[Optional()]
    )


class BaseAdminUnitForm(FlaskForm):
    name = HTML5StringField(
        lazy_gettext("Name"), validators=[DataRequired(), Length(min=5, max=255)]
    )
    short_name = HTML5StringField(
        lazy_gettext("Short name"),
        description=lazy_gettext(
            "The short name is used to create a unique identifier for your events"
        ),
        validators=[
            DataRequired(),
            Length(min=5, max=100),
            Regexp(
                r"^\w+$",
                message=lazy_gettext(
                    "Short name must contain only letters numbers or underscore"
                ),
            ),
        ],
    )
    url = URLField(lazy_gettext("Link URL"), validators=[Optional()])
    email = EmailField(lazy_gettext("Email"), validators=[Optional()])
    phone = TelField(lazy_gettext("Phone"), validators=[Optional()])
    fax = TelField(lazy_gettext("Fax"), validators=[Optional()])
    logo = FormField(Base64ImageForm, lazy_gettext("Logo"), default=lambda: Image())
    location = FormField(AdminUnitLocationForm, default=lambda: Location())

    incoming_verification_requests_allowed = BooleanField(
        lazy_gettext("Allow verification requests"),
        description=lazy_gettext(
            "If set, unverified organizations may ask you for verification."
        ),
        validators=[Optional()],
    )
    incoming_verification_requests_text = TextAreaField(
        lazy_gettext("Verification requests information"),
        validators=[Optional()],
        description=lazy_gettext(
            "This text is shown to unverified organizations to help them decide whether they ask you for verification."
        ),
    )

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:  # pragma: no cover
                obj.location = Location()
            elif name == "logo" and not obj.logo:
                obj.logo = Image()
            field.populate_obj(obj, name)


class AdminUnitRelationForm(FlaskForm):
    verify = BooleanField(
        lazy_gettext("Verify new organization"),
        description=lazy_gettext(
            "If set, events of the new organization are publicly visible."
        ),
        validators=[Optional()],
    )
    auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the new organization are verified automatically."
        ),
        validators=[Optional()],
    )


class CreateAdminUnitForm(BaseAdminUnitForm):
    embedded_relation = FormField(
        AdminUnitRelationForm, default=lambda: AdminUnitRelation()
    )
    submit = SubmitField(lazy_gettext("Create organization"))

    def populate_obj(self, obj):
        super().populate_obj(obj)
        delattr(obj, "embedded_relation")


class UpdateAdminUnitForm(BaseAdminUnitForm):
    submit = SubmitField(lazy_gettext("Update settings"))


class UpdateAdminUnitWidgetForm(FlaskForm):
    widget_font = StringField(lazy_gettext("Font"), validators=[Optional()])
    widget_background_color = StringField(
        lazy_gettext("Background Color"),
        default="#ffffff",
        widget=ColorInput(),
        validators=[Optional()],
    )
    widget_primary_color = StringField(
        lazy_gettext("Primary Color"),
        default="#007bff",
        widget=ColorInput(),
        validators=[Optional()],
    )
    widget_link_color = StringField(
        lazy_gettext("Link Color"),
        default="#007bff",
        widget=ColorInput(),
        validators=[Optional()],
    )
    submit = SubmitField(lazy_gettext("Update settings"))


class RequestAdminUnitDeletionForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Request deletion"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])


class CancelAdminUnitDeletionForm(FlaskForm):
    submit = SubmitField(lazy_gettext("Cancel deletion"))
    name = StringField(lazy_gettext("Name"), validators=[DataRequired()])
