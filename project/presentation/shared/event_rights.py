from flask_security import current_user

from project.presentation.shared.access import (
    can_reference_event,
    can_request_event_reference,
    has_access,
)


def event_user_rights(event) -> dict:
    """What the current user may do with an event (read model)."""
    return {
        "can_duplicate_event": has_access(event.admin_unit, "events:write"),
        "can_verify_event": has_access(event.admin_unit, "event:verify"),
        "can_reference_event": can_reference_event(event),
        "can_create_reference_request": can_request_event_reference(event),
        "can_create_event": has_access(event.admin_unit, "events:write"),
        "can_view_actions": current_user.is_authenticated,
        "can_update_event": has_access(event.admin_unit, "events:write"),
    }
