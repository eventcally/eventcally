"""Parity of the API key pages (manage and user). Written against the ORM path
first."""

from sqlalchemy import text


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _first_cells(utils, response):
    soup = utils.get_soup(response)
    return [
        next(row.find("td").stripped_strings) for row in soup.select("table tbody tr")
    ]


def _insert_key(app, db, name, created_at, user_id=None, admin_unit_id=None):
    with app.app_context():
        from project.models import ApiKey

        api_key = ApiKey(name=name, user_id=user_id, admin_unit_id=admin_unit_id)
        api_key.generate_key()
        db.session.add(api_key)
        db.session.commit()
        db.session.execute(
            text("UPDATE apikey SET created_at = :created_at WHERE id = :id"),
            {"created_at": created_at, "id": api_key.id},
        )
        db.session.commit()
        return api_key.id


def test_user_list_sorts(app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    _insert_key(app, db, "bravo", "2026-01-02", user_id=user_id)
    _insert_key(app, db, "Alpha", "2026-01-01", user_id=user_id)
    _insert_key(app, db, "charlie", "2026-01-03", user_id=user_id)
    other_user_id = seeder.create_user("other@test.de")
    _insert_key(app, db, "foreign", "2026-01-04", user_id=other_user_id)

    response = utils.get_ok(utils.get_url("user.api_keys"))
    assert _first_cells(utils, response) == ["Alpha", "bravo", "charlie"]

    response = utils.get_ok(utils.get_url("user.api_keys", sort="-created_at"))
    assert _first_cells(utils, response) == ["charlie", "bravo", "Alpha"]


def test_manage_list_and_pages(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    key_id = _insert_key(app, db, "Org key", "2026-01-02", admin_unit_id=admin_unit_id)
    _insert_key(app, db, "User key", "2026-01-02", user_id=user_id)

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.api_keys", id=admin_unit_id)
    )
    assert _first_cells(utils, response) == ["Org key"]

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.api_key", id=admin_unit_id, api_key_id=key_id)
    )
    text_ = _text(utils, response)
    assert "Org key" in text_
    assert "500 per 1 hour" in text_

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.api_key_update", id=admin_unit_id, api_key_id=key_id
        )
    )
    assert utils.get_soup(response).find("input", attrs={"name": "name"})["value"] == (
        "Org key"
    )

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.api_key_delete", id=admin_unit_id, api_key_id=key_id
        )
    )
    assert f"Möchtest du 'API Schlüssel {key_id}' löschen?" in _text(utils, response)


def test_foreign_keys_are_unauthorized(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    foreign_key_id = _insert_key(
        app, db, "foreign", "2026-01-04", user_id=other_user_id
    )
    org_key_id = _insert_key(
        app, db, "Org key", "2026-01-02", admin_unit_id=admin_unit_id
    )
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(utils.get_url("user.api_key", api_key_id=foreign_key_id))
    utils.get_unauthorized(utils.get_url("user.api_key", api_key_id=org_key_id))
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.api_key", id=other_admin_unit_id, api_key_id=org_key_id
        )
    )
    utils.assert_response_notFound(
        utils.get(utils.get_url("user.api_key", api_key_id=4711))
    )
