from enum import Enum

from flask_babel import lazy_gettext


class PermissionDomain(Enum):
    user = 1
    organization = 2


class PermissionAction(Enum):
    read = 1
    write = 2


class PermissionInfo:  # pragma: no cover
    def __init__(
        self,
        domain: PermissionDomain,
        entity: str,
        action: PermissionAction,
        entity_display_name: str,
        no_api_access: bool = False,
    ):
        self.domain = domain
        self.entity = entity
        self.action = action
        self.entity_display_name = entity_display_name
        self.permission = f"{entity}:{action.name}"
        self.full_permission = f"{domain.name}.{self.permission}"
        self.no_api_access = no_api_access
        self.domain_label = PermissionInfo._get_domain_label(domain)
        self.label = PermissionInfo._get_label(entity_display_name, action)
        self.full_label = PermissionInfo._get_full_label(
            self.domain_label, entity_display_name, action
        )

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

    @staticmethod
    def _get_domain_label(domain: PermissionDomain):
        if domain == PermissionDomain.user:
            return lazy_gettext("User")
        elif domain == PermissionDomain.organization:
            return lazy_gettext("Organization")
        else:
            raise ValueError(f"Unknown domain: {domain}")

    @staticmethod
    def _get_label(entity_display_name: str, action: PermissionAction):
        if action == PermissionAction.read:
            return lazy_gettext(
                "Read %(entity_display_name)s", entity_display_name=entity_display_name
            )
        elif action == PermissionAction.write:
            return lazy_gettext(
                "Write %(entity_display_name)s", entity_display_name=entity_display_name
            )
        else:
            raise ValueError(f"Unknown action: {action}")

    @staticmethod
    def _get_full_label(
        domain_label: str, entity_display_name: str, action: PermissionAction
    ):
        return lazy_gettext(
            "%(domain_label)s: %(label)s",
            domain_label=domain_label,
            label=PermissionInfo._get_label(entity_display_name, action),
        )


permission_infos: list[PermissionInfo] = list()


def _add_permission_info(
    domain: PermissionDomain,
    entity: str,
    entity_display_name: str,
    actions=[PermissionAction.read, PermissionAction.write],
    no_api_access: bool = False,
):
    for action in actions:
        permission_infos.append(
            PermissionInfo(
                domain,
                entity,
                action,
                entity_display_name,
                no_api_access=no_api_access,
            )
        )


def _add_org(
    entity: str,
    entity_display_name: str,
    actions=[PermissionAction.read, PermissionAction.write],
    no_api_access: bool = False,
):
    _add_permission_info(
        PermissionDomain.organization,
        entity,
        entity_display_name,
        actions=actions,
        no_api_access=no_api_access,
    )


def _add_user(
    entity: str,
    entity_display_name: str,
    actions=[PermissionAction.read, PermissionAction.write],
    no_api_access: bool = False,
):
    _add_permission_info(
        PermissionDomain.user,
        entity,
        entity_display_name,
        actions=actions,
        no_api_access=no_api_access,
    )


_add_org("api_keys", lazy_gettext("API keys"), no_api_access=True)
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

_add_user("api_keys", lazy_gettext("API keys"), no_api_access=True)
_add_user("organization_invitations", lazy_gettext("Organization invitations"))
_add_user("favorite_events", lazy_gettext("Favorite events"))
