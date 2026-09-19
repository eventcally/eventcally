from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class CreateCustomWidgetHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateCustomWidgetCommand, uow: AbstractUnitOfWork):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "custom_widgets:write", uow
        )

        custom_widget = CustomWidgetAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            widget_type=cmd.widget_type,
            name=cmd.name,
            settings=cmd.settings,
        )
        uow.custom_widgets.add(custom_widget)

        return commands.CreateCustomWidgetCommandResult(id=custom_widget.id)
