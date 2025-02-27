from flask_babel import gettext

from project.modular.base_views import BaseDeleteView
from project.views.admin_blueprint.organization.forms import DeleteForm
from project.views.utils import flash_non_match_for_deletion


class DeleteView(BaseDeleteView):
    form_class = DeleteForm

    def can_object_be_deleted(self, form, object):
        return flash_non_match_for_deletion(
            form.name.data,
            object.name,
            gettext("Entered name does not match organization name"),
        )
