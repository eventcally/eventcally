from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .custom_widget_utils import ensure_custom_widget_exists


class UpdateCustomWidgetHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateCustomWidgetCommand, uow: AbstractUnitOfWork):
        custom_widget = ensure_custom_widget_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, custom_widget.admin_unit_id, "custom_widgets:write", uow
        )

        custom_widget.update(
            actor=cmd.actor,
            widget_type=cmd.widget_type,
            name=cmd.name,
            settings=cmd.settings,
        )
        uow.custom_widgets.update(custom_widget)
