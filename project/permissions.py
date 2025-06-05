from enum import Enum

from flask_babel import lazy_gettext


class PermissionAction(Enum):
    read = 1
    write = 2


class PermissionInfo:  # pragma: no cover
    def __init__(self, entity: str, action: PermissionAction, entity_display_name: str):
        self.entity = entity
        self.action = action
        self.entity_display_name = entity_display_name
        self.permission = f"{entity}:{action.name}"

    def __str__(self):
        return self.permission

    def __hash__(self):
        return hash(self.permission)

    def __eq__(self, value):
        return (
            self.permission == value.permission
            if isinstance(value, PermissionInfo)
            else False
        )

    @property
    def display_action(self):
        if self.action == PermissionAction.read:
            return lazy_gettext("Read")
        elif self.action == PermissionAction.write:
            return lazy_gettext("Write")
        else:
            raise ValueError(f"Unknown action: {self.action}")


organization_permission_infos = list()


def get_organization_permission_info(
    permission: str,
) -> PermissionInfo | None:  # pragma: no cover
    return next(
        (
            info
            for info in organization_permission_infos
            if info.permission == permission
        ),
        None,
    )


def _add_org(
    entity: str,
    entity_display_name: str,
    actions=[PermissionAction.read, PermissionAction.write],
):
    for action in actions:
        organization_permission_infos.append(
            PermissionInfo(
                entity,
                action,
                entity_display_name,
            )
        )


_add_org("api_keys", lazy_gettext("API keys"))
_add_org("custom_widgets", lazy_gettext("Custom widgets"))
_add_org("event_lists", lazy_gettext("Event lists"))
_add_org("event_organizers", lazy_gettext("Event organizers"))
_add_org("event_places", lazy_gettext("Places"))
_add_org("events", lazy_gettext("Events"))
_add_org("export", lazy_gettext("Export"), [PermissionAction.read])
_add_org(
    "incoming_organization_verification_requests",
    lazy_gettext("Incoming verification requests"),
)
_add_org(
    "incoming_event_reference_requests", lazy_gettext("Incoming reference requests")
)
_add_org("incoming_event_references", lazy_gettext("Incoming references"))
_add_org("organization_invitations", lazy_gettext("Organization invitations"))
_add_org(
    "organization_member_invitations", lazy_gettext("Organization member invitations")
)
_add_org("organization_members", lazy_gettext("Organization members"))
_add_org("settings", lazy_gettext("Settings"))
_add_org(
    "outgoing_organization_verification_requests",
    lazy_gettext("Outgoing verification requests"),
)
_add_org(
    "outgoing_event_reference_requests", lazy_gettext("Outgoing reference requests")
)
_add_org("outgoing_event_references", lazy_gettext("Outgoing references"))
_add_org(
    "outgoing_organization_relations", lazy_gettext("Outgoing organization relations")
)
_add_org("widgets", lazy_gettext("Widgets"))
