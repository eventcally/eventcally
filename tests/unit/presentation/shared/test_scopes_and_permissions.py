from project.presentation.shared import permissions, scopes


def test_permission_info_str_hash_and_equality():
    info = permissions.PermissionInfo(
        permissions.PermissionDomain.organization,
        "events",
        permissions.PermissionAction.read,
        "Events",
    )
    same = permissions.PermissionInfo(
        permissions.PermissionDomain.user,
        "events",
        permissions.PermissionAction.read,
        "Events",
    )

    assert str(info) == "events:read"
    assert info.full_permission == "organization.events:read"
    assert hash(info) == hash(same)
    assert info == same
    assert info != "events:read"


def test_get_organization_permission_infos():
    infos = permissions.get_organization_permission_infos(["events:write", "nope"])

    assert [info.full_permission for info in infos] == ["organization.events:write"]


def test_api_permissions_exclude_no_api_access():
    assert not any(info.no_api_access for info in permissions.api_permission_infos)


def test_every_api_permission_is_a_scope():
    assert "organization.events:write" in scopes.scope_list
    assert "openid" in scopes.scopes


def test_replace_legacy_scopes():
    assert (
        scopes.replace_legacy_scopes("openid event:write")
        == "openid organization.events:write"
    )
    assert scopes.replace_legacy_scopes("openid") == "openid"
    assert scopes.replace_legacy_scopes("") == ""
    assert scopes.replace_legacy_scopes(None) is None
