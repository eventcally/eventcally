from project.views.user_blueprint.oauth2_client.views import (
    CreateView as UserCreateView,
)
from project.views.utils import current_admin_unit


class CreateView(UserCreateView):
    def build_create_command(self, form):
        return form.create_create_command(admin_unit_id=current_admin_unit.id)
