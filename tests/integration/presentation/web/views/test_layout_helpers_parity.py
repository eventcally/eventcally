"""Parity of the template helpers used by the layouts (manage bar badges, Vue
`currentAdminUnit` grants, ToS link, announcement). Written against the ORM path first."""

import re


def _badges(utils, response):
    soup = utils.get_soup(response)
    return [span.get_text().strip() for span in soup.select("span.badge-pill")]


def _vue_list(response, key):
    text = response.data.decode()
    unit = text[text.index('vue_app_data["currentAdminUnit"]') :]
    block = re.search(key + r": \[(.*?)\]", unit, re.S).group(1)
    return set(re.findall(r'"([^"]+)"', block))


def _seed_incoming_requests(seeder, admin_unit_id):
    other_user_id = seeder.create_user("source@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Source Crew")
    event_id = seeder.create_event(other_admin_unit_id)
    seeder.create_reference_request(event_id, admin_unit_id)
    event_id_2 = seeder.create_event(other_admin_unit_id)
    seeder.create_reference_request(event_id_2, admin_unit_id)
    done_event_id = seeder.create_event(other_admin_unit_id)
    done_id = seeder.create_reference_request(done_event_id, admin_unit_id)
    seeder.create_admin_unit_verification_request(other_admin_unit_id, admin_unit_id)
    return done_id


def _verify_reference_request(app, db, request_id):
    with app.app_context():
        from project.infrastructure.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        request = db.session.get(EventReferenceRequest, request_id)
        request.review_status = EventReferenceRequestReviewStatus.verified
        db.session.commit()


def test_manage_bar_without_requests_has_no_badge(seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_ok(utils.get_url("manage_admin_unit.events", id=admin_unit_id))

    assert _badges(utils, response) == []


def test_manage_bar_badges_count_inbox_requests(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    done_id = _seed_incoming_requests(seeder, admin_unit_id)
    _verify_reference_request(app, db, done_id)

    response = utils.get_ok(utils.get_url("manage_admin_unit.events", id=admin_unit_id))

    # reference badge (dropdown + collapsed duplicate), verification badge likewise
    assert sorted(set(_badges(utils, response))) == ["1", "2"]
    assert response.data.decode().count("badge-pill") >= 2


def test_manage_bar_badges_visible_to_event_verifier(app, db, seeder, utils):
    owner_id, admin_unit_id, _ = seeder.setup_base_event_verifier()
    done_id = _seed_incoming_requests(seeder, admin_unit_id)
    _verify_reference_request(app, db, done_id)

    response = utils.get_ok(utils.get_url("manage_admin_unit.events", id=admin_unit_id))

    assert sorted(set(_badges(utils, response))) == ["1", "2"]


def test_vue_current_admin_unit_grants_of_owner(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/custom-widgets")

    with app.app_context():
        from project.infrastructure.models import AdminUnitMemberRole

        roles = db.session.query(AdminUnitMemberRole).all()
        expected_roles = {
            r.name for r in roles if r.name in ("admin", "event_verifier")
        }
        expected_permissions = set()
        for role in roles:
            expected_permissions.update(role.permissions)

    assert _vue_list(response, "roles") == expected_roles == {"admin", "event_verifier"}
    assert _vue_list(response, "permissions") == expected_permissions
    assert "custom_widgets:read" in expected_permissions


def test_vue_current_admin_unit_grants_of_event_verifier(seeder, utils):
    seeder.setup_base_event_verifier()

    response = utils.get_ok("/organizers")

    assert _vue_list(response, "roles") == {"event_verifier"}
    assert "events:write" in _vue_list(response, "permissions")
    assert "settings:write" not in _vue_list(response, "permissions")


def test_vue_current_admin_unit_grants_empty_for_platform_admin_non_member(
    seeder, utils
):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_user("admin@admin.de", admin=True)
    utils.logout()
    utils.login("admin@admin.de")

    response = utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/custom-widgets")

    assert _vue_list(response, "roles") == set()
    assert _vue_list(response, "permissions") == set()


def test_tos_link_and_announcement_follow_settings(app, db, seeder, utils):
    response = utils.get_ok(utils.get_url("main.home"))
    assert utils.get_url("main.tos").encode() not in response.data
    assert b"alert-warning" not in response.data

    with app.app_context():
        from project.infrastructure.init_data import upsert_settings

        settings = upsert_settings()
        settings.tos = "x"
        settings.announcement = "Wartungsarbeiten"
        db.session.commit()

    response = utils.get_ok(utils.get_url("main.home"))
    assert utils.get_url("main.tos").encode() in response.data
    assert b"Wartungsarbeiten" in response.data


def test_empty_announcement_renders_nothing(app, db, utils):
    with app.app_context():
        from project.infrastructure.init_data import upsert_settings

        settings = upsert_settings()
        settings.tos = ""
        settings.announcement = ""
        db.session.commit()

    response = utils.get_ok(utils.get_url("main.home"))

    assert b"alert-warning" not in response.data
    assert utils.get_url("main.tos").encode() not in response.data


def test_rendering_a_page_without_settings_inserts_no_row(app, db, utils):
    utils.get_ok(utils.get_url("main.home"))
    utils.get_ok("/register")

    with app.app_context():
        from project.infrastructure.models import Settings

        assert db.session.query(Settings).count() == 0
