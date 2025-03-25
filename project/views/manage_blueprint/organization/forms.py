from flask_babel import lazy_gettext
from wtforms import FormField
from wtforms.fields import BooleanField
from wtforms.validators import Optional

from project.models import AdminUnitRelation, Image, Location
from project.modular.base_form import BaseCreateForm, BaseForm
from project.views.manage_admin_unit.admin_unit.forms import AdminUnitFormMixin


class AdminUnitRelationForm(BaseForm):
    verify = BooleanField(
        lazy_gettext("Verify new organization"),
        description=lazy_gettext(
            "If set, events of the new organization are publicly visible."
        ),
        validators=[Optional()],
        render_kw={"ri": "checkbox"},
    )
    auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the new organization are verified automatically."
        ),
        validators=[Optional()],
        render_kw={"ri": "checkbox"},
    )


class CreateForm(BaseCreateForm, AdminUnitFormMixin):
    embedded_relation = FormField(
        AdminUnitRelationForm, default=lambda: AdminUnitRelation()
    )

    def populate_obj(self, obj):
        for name, field in self._fields.items():
            if name == "location" and not obj.location:  # pragma: no cover
                obj.location = Location()
            elif name == "logo" and not obj.logo:
                obj.logo = Image()
            field.populate_obj(obj, name)

        if hasattr(obj, "embedded_relation"):
            delattr(obj, "embedded_relation")
