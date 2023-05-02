import os


def test_home(client, seeder, utils):
    url = utils.get_url("home")
    response = utils.get_ok(url)
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers


def test_up(app, utils):
    utils.get_ok("up")


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
    from project import dump_path

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
    runner.invoke(args=["seo", "generate-sitemap"])
    result = runner.invoke(args=["seo", "generate-robots-txt"])
    assert result.exit_code == 0
    utils.get_endpoint_ok("robots_txt")


def test_sitemap_xml(seeder, app, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    app.config["SERVER_NAME"] = "localhost"
    runner = app.test_cli_runner()
    result = runner.invoke(args=["seo", "generate-sitemap"])
    assert result.exit_code == 0
    utils.get_endpoint_ok("sitemap_xml")
