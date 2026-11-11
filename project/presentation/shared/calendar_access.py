from flask import current_app
from flask_security import current_user

from project.application.queries import ListCalendarsQuery, PageRequest
from project.presentation.shared.access import has_access
from project.presentation.shared.current_admin_unit import get_current_admin_unit


def calendar_organization():
    """The session's current organization, if its members may put events into calendars
    (`calendars:write`) and it has at least one to choose from. `None` for anonymous
    visitors and everybody else."""
    if not current_user or not current_user.is_authenticated:
        return None

    admin_unit = get_current_admin_unit()

    if not admin_unit or not has_access(admin_unit, "calendars:write"):
        return None

    page = current_app.container.cqrs.query_bus().handle(
        ListCalendarsQuery(admin_unit_id=admin_unit.id, page=PageRequest(per_page=1))
    )

    if page is None or page.total == 0:
        return None

    return admin_unit
