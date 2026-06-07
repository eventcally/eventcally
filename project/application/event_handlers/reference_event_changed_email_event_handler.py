from project.application.read_repositories.abstract_event_read_repository import (
    AbstractEventReadRepository,
)
from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_event_handler import AbstractEventHandler


class ReferenceEventChangedEmailEventHandler(AbstractEventHandler):
    def __init__(
        self,
        organization_service: OrganizationApplicationService,
        event_read_repo: AbstractEventReadRepository,
    ):
        super().__init__()
        self.organization_service = organization_service
        self.event_read_repo = event_read_repo

    def handle(self, event: events.EventUpdated, uow: AbstractUnitOfWork):
        with uow:
            event_instance = uow.events.get(event.id)

            if not event_instance:  # pragma: no cover
                return

            if not self._has_significant_changes(event):
                return

            references = uow.event_references.get_by_event_id(event_instance.id)

            if not references:
                return

            event_read_model = self.event_read_repo.get(event_instance.id)
            for reference in references:
                # Alle Mitglieder der AdminUnit, die das Recht haben, Requests zu verifizieren
                self.organization_service.send_template_mails_to_members_async(
                    uow,
                    reference.admin_unit_id,
                    "incoming_event_reference_requests:write",
                    "referenced_event_changed_notice",
                    event=event_read_model,
                    reference=reference,
                )

    def _has_significant_changes(self, event: events.EventUpdated) -> bool:
        return (
            event.name
            or event.status
            or event.attendance_mode
            or event.booked_up
            or event.event_place_id
            or event.organizer_id
            or event.date_definitions
        )
