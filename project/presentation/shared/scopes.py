from project.presentation.shared.permissions import api_permission_infos
from project.shared.utils import get_localized_scope

scope_list = [
    "openid",
    "profile",
]
scopes = {k: get_localized_scope(k) for v, k in enumerate(scope_list)}

for permission_info in api_permission_infos:
    permission = permission_info.full_permission
    scope_list.append(permission)
    scopes[permission] = permission_info.full_label


legacy_scope_mapping = {
    "organizer:write": "organization.event_organizers:write",
    "place:write": "organization.event_places:write",
    "event:write": "organization.events:write",
    "user:read": "user.organization_invitations:read",
    "user:write": "user.organization_invitations:write",
}


def replace_legacy_scopes(scope: str) -> str:
    if scope:
        for legacy_scope, new_scope in legacy_scope_mapping.items():
            if legacy_scope in scope:
                scope = scope.replace(legacy_scope, new_scope)

    return scope
