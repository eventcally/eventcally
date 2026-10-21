"""The audit line ("Created at … by …") under read/update displays. Written against
the ORM path first: query-backed pages must still show it."""

import re

from sqlalchemy import text

from tests.integration.presentation.web.views.manage_admin_unit.test_webhook_delivery import (  # noqa: F401
    _create_webhook_delivery,
)


def _audit(utils, response):
    marker = utils.get_soup(response).find(string=re.compile(r"Erstellt am \d"))
    return " ".join(marker.parent.get_text().split()) if marker else None


def _stamp(app, db, table, object_id, user_id):
    with app.app_context():
        db.session.execute(
            text(
                f"UPDATE {table} SET created_at = '2026-01-02 10:00',"
                " updated_at = '2026-01-03 11:00',"
                " created_by_id = :user_id, updated_by_id = :user_id WHERE id = :id"
            ),
            {"id": object_id, "user_id": user_id},
        )
        db.session.commit()


EXPECTED = (
    "Erstellt am 02.01.26, 11:00 von test@test.de."
    " Zuletzt aktualisiert am 03.01.26, 12:00 von test@test.de."
)


def _pages(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Andere Crew")
    pages = {}

    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)
    _stamp(app, db, "adminunitinvitation", invitation_id, user_id)
    pages["organization_invitation_update"] = utils.get_url(
        "manage_admin_unit.organization_invitation_update",
        id=admin_unit_id,
        organization_invitation_id=invitation_id,
    )

    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    _stamp(app, db, "apikey", api_key_id, user_id)
    pages["api_key_read"] = utils.get_url(
        "manage_admin_unit.api_key", id=admin_unit_id, api_key_id=api_key_id
    )

    relation_id = seeder.create_admin_unit_relation(admin_unit_id, other_admin_unit_id)
    _stamp(app, db, "adminunitrelation", relation_id, user_id)
    pages["relation_update"] = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_update",
        id=admin_unit_id,
        organization_relation_id=relation_id,
    )

    verification_id = seeder.create_admin_unit_verification_request(
        admin_unit_id, other_admin_unit_id
    )
    _stamp(app, db, "adminunitverificationrequest", verification_id, user_id)
    pages["verification_request_read"] = utils.get_url(
        "manage_admin_unit.outgoing_organization_verification_request",
        id=admin_unit_id,
        organization_verification_request_id=verification_id,
    )

    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    _stamp(app, db, "oauth2_client", client_id, user_id)
    pages["oauth2_client_read"] = utils.get_url(
        "manage_admin_unit.oauth2_client",
        id=admin_unit_id,
        oauth2_client_id=client_id,
    )

    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    _stamp(app, db, "oauth2_client", app_id, user_id)
    pages["app_read"] = utils.get_url(
        "manage_admin_unit.app", id=admin_unit_id, app_id=app_id
    )

    _, app_key_id = seeder.insert_app_key(app_id)
    _stamp(app, db, "app_key", app_key_id, user_id)
    pages["app_key_read"] = utils.get_url(
        "manage_admin_unit.app.app_key",
        id=admin_unit_id,
        app_id=app_id,
        app_key_id=app_key_id,
    )

    installation_id = seeder.install_app(app_id, admin_unit_id)
    _stamp(app, db, "app_installation", installation_id, user_id)
    pages["app_installation_read"] = utils.get_url(
        "manage_admin_unit.app_installation",
        id=admin_unit_id,
        app_installation_id=installation_id,
    )

    event_id = seeder.create_event(other_admin_unit_id)
    reference_id = seeder.create_reference(event_id, admin_unit_id)
    _stamp(app, db, "eventreference", reference_id, user_id)
    pages["incoming_reference_read"] = utils.get_url(
        "manage_admin_unit.incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )

    own_event_id = seeder.create_event(admin_unit_id)
    request_id = seeder.create_reference_request(own_event_id, other_admin_unit_id)
    _stamp(app, db, "eventreferencerequest", request_id, user_id)
    pages["outgoing_reference_request_read"] = utils.get_url(
        "manage_admin_unit.outgoing_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=request_id,
    )

    return pages


def test_audit_lines(app, db, seeder, utils):
    pages = _pages(app, db, seeder, utils)

    actual = {key: _audit(utils, utils.get_ok(url)) for key, url in pages.items()}

    assert actual == {key: EXPECTED for key in pages}
