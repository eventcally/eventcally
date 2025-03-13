from flask_babel import lazy_gettext
from sqlalchemy import func
from wtforms import BooleanField
from wtforms.validators import DataRequired

from project import db
from project.models.admin_unit import AdminUnit, AdminUnitRelation
from project.modular.ajax import AjaxModelLoader
from project.modular.base_form import BaseCreateForm, BaseListForm, BaseUpdateForm
from project.modular.fields import AjaxSelectField
from project.modular.filters import BooleanFilter
from project.modular.search_definition import SearchDefinition
from project.modular.sort_definition import SortDefinition
from project.services.admin_unit import get_admin_unit_query
from project.services.search_params import AdminUnitSearchParams
from project.views.utils import current_admin_unit


class OrganizationAjaxModelLoader(AjaxModelLoader):
    def __init__(self, **options):
        options["fields"] = [AdminUnit.name]
        super().__init__(db.session, AdminUnit, **options)

    def get_pagination(self, term):
        params = AdminUnitSearchParams()
        params.keyword = term
        params.include_unverified = current_admin_unit.can_verify_other

        pagination = get_admin_unit_query(params).paginate()
        return pagination


class SharedFormMixin(object):
    verify = BooleanField(
        lazy_gettext("Verify other organization"),
        description=lazy_gettext(
            "If set, events of the other organization are publicly visible."
        ),
        render_kw={"ri": "switch"},
    )
    auto_verify_event_reference_requests = BooleanField(
        lazy_gettext("Verify reference requests automatically"),
        description=lazy_gettext(
            "If set, all upcoming reference requests of the other organization are verified automatically."
        ),
        render_kw={"ri": "switch"},
    )


class CreateForm(BaseCreateForm, SharedFormMixin):
    target_admin_unit = AjaxSelectField(
        OrganizationAjaxModelLoader(),
        lazy_gettext("Other organization"),
        validators=[DataRequired()],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.move_field_to_top("target_admin_unit")


class UpdateForm(BaseUpdateForm, SharedFormMixin):
    pass


class ListForm(BaseListForm):
    filters = [
        BooleanFilter(
            AdminUnitRelation.verify, label=lazy_gettext("Verify other organization")
        ),
        BooleanFilter(
            AdminUnitRelation.auto_verify_event_reference_requests,
            label=lazy_gettext("Verify reference requests automatically"),
        ),
    ]
    search_definitions = [SearchDefinition(AdminUnit.name)]
    sort_definitions = [
        SortDefinition(AdminUnit.name, func=func.lower, label=lazy_gettext("Name")),
        SortDefinition(
            AdminUnit.last_modified_at,
            desc=True,
            label=lazy_gettext("Last modified first"),
        ),
    ]
