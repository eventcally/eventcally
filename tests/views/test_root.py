import os

from project import dump_path


def test_home(client, seeder, utils):
    url = utils.get_url("home")
    utils.get_ok(url)

    url = utils.get_url("home", src="infoscreen")
    response = client.get(url)
    utils.assert_response_redirect(response, "home")


def test_example(client, seeder, utils):
    url = utils.get_url("example")
    utils.get_ok(url)


def test_tos(app, db, utils):
    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        settings.tos = "Meine Nutzungsbedingungen"
        db.session.commit()

    url = utils.get_url("tos")
    response = utils.get_ok(url)
    assert b"Meine Nutzungsbedingungen" in response.data


def test_legal_notice(app, db, utils):
    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        settings.legal_notice = "Mein Impressum"
        db.session.commit()

    url = utils.get_url("legal_notice")
    response = utils.get_ok(url)
    assert b"Mein Impressum" in response.data


def test_contact(app, db, utils):
    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        settings.contact = "Mein Kontakt"
        db.session.commit()

    url = utils.get_url("contact")
    response = utils.get_ok(url)
    assert b"Mein Kontakt" in response.data


def test_privacy(app, db, utils):
    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        settings.privacy = "Mein Datenschutz"
        db.session.commit()

    url = utils.get_url("privacy")
    response = utils.get_ok(url)
    assert b"Mein Datenschutz" in response.data


def test_developer(client, seeder, utils):
    file_name = "all.zip"
    all_path = os.path.join(dump_path, file_name)

    if os.path.exists(all_path):
        os.remove(all_path)

    url = utils.get_url("developer")
    utils.get_ok(url)


def test_favicon(app, utils):
    utils.get_ok("favicon.ico")


def test_robots_txt(app, utils):
    app.config["SERVER_NAME"] = "localhost"
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seo", "generate-robots-txt"])
    assert "Generated robots.txt" in result.output
    utils.get_endpoint_ok("robots_txt")


def test_sitemap_xml(seeder, app, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    app.config["SERVER_NAME"] = "localhost"
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seo", "generate-sitemap"])
    assert "Generated sitemap" in result.output
    utils.get_endpoint_ok("sitemap_xml")
