from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit
from .organization_utils import ensure_organization_exists


class UpdateOrganizationWidgetSettingsHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.UpdateOrganizationWidgetSettingsCommand,
        uow: AbstractUnitOfWork,
    ):
        organization = ensure_organization_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, organization.id, "widgets:write", uow
        )

        organization.update(
            actor=cmd.actor,
            widget_font=cmd.widget_font,
            widget_background_color=cmd.widget_background_color,
            widget_primary_color=cmd.widget_primary_color,
            widget_link_color=cmd.widget_link_color,
        )
        uow.organizations.update(organization)
