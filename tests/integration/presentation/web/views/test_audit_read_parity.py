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
    pages = {}

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

    # The reference, verification request, API key and OAuth2 client pages are Vue
    # pages: their audit comes from the BFF.

    return pages


def test_audit_lines(app, db, seeder, utils):
    pages = _pages(app, db, seeder, utils)

    actual = {key: _audit(utils, utils.get_ok(url)) for key, url in pages.items()}

    assert actual == {key: EXPECTED for key in pages}
