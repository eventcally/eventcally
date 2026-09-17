from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.settings_aggregate import SettingsAggregate

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin


class UpdatePlanningSettingsHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdatePlanningSettingsCommand, uow: AbstractUnitOfWork
    ):
        ensure_actor_is_platform_admin(cmd.actor, uow)

        settings = uow.settings.get()
        if settings is None:
            settings = SettingsAggregate.create(actor=cmd.actor)
            uow.settings.add(settings)

        settings.update(
            actor=cmd.actor,
            planning_external_calendars=cmd.planning_external_calendars,
        )
        uow.settings.update(settings)
