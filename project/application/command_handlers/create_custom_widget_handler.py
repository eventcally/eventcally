from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.custom_widget_aggregate import (
    CustomWidgetAggregate,
)

from .abstract_command_handler import AbstractCommandHandler


class CreateCustomWidgetHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateCustomWidgetCommand, uow: AbstractUnitOfWork):
        custom_widget = CustomWidgetAggregate.create(
            actor=cmd.actor,
            admin_unit_id=cmd.admin_unit_id,
            widget_type=cmd.widget_type,
            name=cmd.name,
            settings=cmd.settings,
        )
        uow.custom_widgets.add(custom_widget)

        return commands.CreateCustomWidgetCommandResult(id=custom_widget.id)
