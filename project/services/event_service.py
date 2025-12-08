from project.models import Event, EventPublicStatus, EventStatus
from project.models.event_reference import EventReference
from project.services.base_service import BaseService
from project.services.event import (
    get_significant_event_changes,
    update_event_dates_with_recurrence_rule,
)
from project.views.utils import send_template_mails_to_admin_unit_members_async


class EventService(BaseService[Event]):

    def insert_object(self, object: Event):
        if not object.status:
            object.status = EventStatus.scheduled

        if not object.public_status:
            object.public_status = EventPublicStatus.published

        update_event_dates_with_recurrence_rule(object)
        super().insert_object(object)

    def update_object(self, object: Event):
        from project import db

        # TODO: Find a better way to handle this without importing db here
        with db.session.no_autoflush:
            update_event_dates_with_recurrence_rule(object)

        changes = get_significant_event_changes(object)
        super().update_object(object)

        if changes:
            self._send_referenced_event_changed_mails(object)

    def _send_referenced_event_changed_mails(self, event):
        # Alle Referenzen
        references = EventReference.query.filter(
            EventReference.event_id == event.id
        ).all()
        for reference in references:
            # Alle Mitglieder der AdminUnit, die das Recht haben, Requests zu verifizieren
            send_template_mails_to_admin_unit_members_async(
                reference.admin_unit_id,
                "incoming_event_reference_requests:write",
                "referenced_event_changed_notice",
                event=event,
                reference=reference,
            )
