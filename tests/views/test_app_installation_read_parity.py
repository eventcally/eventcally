"""Parity of the app installation pages. Written against the ORM path first."""


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def _app(app, db, seeder, admin_unit_id):
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        from project.models import OAuth2Client

        client = db.session.get(OAuth2Client, app_id)
        client.homepage_url = "https://example.com"
        client.description = "Eine App"
        db.session.commit()

    return app_id


def test_install_page_shows_app(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Andere Crew")
    app_id = _app(app, db, seeder, other_admin_unit_id)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app_installations_install",
            id=admin_unit_id,
            app_id=app_id,
        )
    )
    text = _text(utils, response)
    assert "Do you want to install 'Mein Client'?" in text
    assert "https://example.com" in text
    assert "Eine App" in text

    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.app_installations_install",
                id=admin_unit_id,
                app_id=4711,
            )
        )
    )


def test_installation_pages(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    app_id = _app(app, db, seeder, admin_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.app_installations", id=admin_unit_id)
    )
    assert _rows(utils, response)[0].startswith("Mein Client")

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app_installation",
            id=admin_unit_id,
            app_installation_id=installation_id,
        )
    )
    assert "Mein Client" in _text(utils, response)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app_installation_accept_permissions",
            id=admin_unit_id,
            app_installation_id=installation_id,
        )
    )
    assert (
        len(utils.get_soup(response).find_all("input", attrs={"name": "permissions"}))
        > 1
    )

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app_installation_delete",
            id=admin_unit_id,
            app_installation_id=installation_id,
        )
    )
    assert f"Möchtest du 'App installation {installation_id}' löschen?" in _text(
        utils, response
    )

    other_admin_unit_id = seeder.create_admin_unit(user_id, "Andere Crew")
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app_installation",
            id=other_admin_unit_id,
            app_installation_id=installation_id,
        )
    )
