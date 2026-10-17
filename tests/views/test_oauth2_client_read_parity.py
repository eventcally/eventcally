"""Parity of the OAuth2 client and app pages. Written against the ORM path first."""


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
        from project.models import OAuth2Client, Webhook

        client = db.session.get(OAuth2Client, oauth2_client_id)
        client.description = "Beschreibung"
        client.homepage_url = "https://example.com"
        client.webhook = Webhook(
            url="https://hook.example.com",
            secret="geheim",
            event_types=["app.installed"],
        )
        db.session.commit()


def test_user_client_pages(seeder, utils):
    user_id, _ = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(user_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.insert_default_oauth2_client(other_user_id)

    response = utils.get_ok(utils.get_url("user.oauth2_clients"))
    assert _first_cells(utils, response) == ["Mein Client"]

    response = utils.get_ok(
        utils.get_url("user.oauth2_client", oauth2_client_id=client_id)
    )
    text = _text(utils, response)
    assert "authorization_code, refresh_token, client_credentials" in text
    assert "client_secret_basic, client_secret_post, none" in text
    assert "Mein Client" in text

    response = utils.get_ok(
        utils.get_url("user.oauth2_client_update", oauth2_client_id=client_id)
    )
    soup = utils.get_soup(response)
    assert soup.find("input", attrs={"name": "client_name"})["value"] == "Mein Client"
    assert (
        soup.find("textarea", attrs={"name": "redirect_uris"})
        .text.strip()
        .endswith("/oauth2-redirect.html")
    )
    assert "openid" in _checked(soup, "scope")

    response = utils.get_ok(
        utils.get_url("user.oauth2_client_delete", oauth2_client_id=client_id)
    )
    assert "Möchtest du 'Mein Client' löschen?" in _text(utils, response)


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
    assert "https://hook.example.com" in text
    assert "https://example.com" in text
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
