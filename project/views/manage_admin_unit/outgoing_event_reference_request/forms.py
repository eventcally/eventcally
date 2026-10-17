from flask_babel import lazy_gettext
from wtforms.validators import DataRequired

from project.views.manage_admin_unit.ajax import OrganizationAjaxModelLoader
from project.views.modular.base_form import BaseCreateForm
from project.views.modular.fields import AjaxSelectField


class CreateForm(BaseCreateForm):
    admin_unit = AjaxSelectField(
        OrganizationAjaxModelLoader(for_reference_request=True),
        lazy_gettext("Other organization"),
        validators=[DataRequired()],
    )
