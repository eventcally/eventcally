"""Parity of the OAuth2 client and app pages. Written against the ORM path first."""

import re


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _first_cells(utils, response):
    soup = utils.get_soup(response)
    return [
        next(row.find("td").stripped_strings) for row in soup.select("table tbody tr")
    ]


def _checked(soup, name):
    return sorted(
        box["value"]
        for box in soup.find_all("input", attrs={"name": name})
        if box.has_attr("checked")
    )


def _set_webhook(app, db, oauth2_client_id):
    with app.app_context():
        from project.infrastructure.models import OAuth2Client, Webhook

        client = db.session.get(OAuth2Client, oauth2_client_id)
        client.description = "Beschreibung"
        client.homepage_url = "https://example.com"
        client.webhook = Webhook(
            url="https://hook.example.com",
            secret="geheim",
            event_types=["app.installed"],
        )
        db.session.commit()


def test_manage_client_list_excludes_apps(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.oauth2_clients", id=admin_unit_id)
    )
    assert len(_first_cells(utils, response)) == 1

    response = utils.get_ok(utils.get_url("manage_admin_unit.apps", id=admin_unit_id))
    assert len(_first_cells(utils, response)) == 1


def test_app_pages(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    _set_webhook(app, db, app_id)

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.app", id=admin_unit_id, app_id=app_id)
    )
    text = _text(utils, response)
    assert re.search(r"https://hook\.example\.com", text)
    assert re.search(r"https://example\.com", text)
    assert "Beschreibung" in text

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.app_update", id=admin_unit_id, app_id=app_id)
    )
    soup = utils.get_soup(response)
    assert soup.find("input", attrs={"name": "webhook-url"})["value"] == (
        "https://hook.example.com"
    )
    assert soup.find("input", attrs={"name": "webhook-secret"})["value"] == "geheim"
    assert _checked(soup, "webhook-event_types") == ["app.installed"]
    assert soup.find("textarea", attrs={"name": "description"}).text.strip() == (
        "Beschreibung"
    )
    assert len(_checked(soup, "app_permissions")) > 1

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.app.app_keys", id=admin_unit_id, app_id=app_id)
    )
    assert "Mein Client" in _text(utils, response)


def test_app_of_other_organization(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url("manage_admin_unit.app", id=other_admin_unit_id, app_id=app_id)
    )
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app.app_keys", id=other_admin_unit_id, app_id=app_id
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.app.app_keys", id=admin_unit_id, app_id=4711
            )
        )
    )
