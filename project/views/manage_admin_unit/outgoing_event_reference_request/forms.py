from flask_babel import lazy_gettext
from wtforms.validators import DataRequired

from project.modular.base_form import BaseCreateForm
from project.modular.fields import AjaxSelectField
from project.views.manage_admin_unit.ajax import OrganizationAjaxModelLoader


class CreateForm(BaseCreateForm):
    admin_unit = AjaxSelectField(
        OrganizationAjaxModelLoader(for_reference_request=True),
        lazy_gettext("Other organization"),
        validators=[DataRequired()],
    )
