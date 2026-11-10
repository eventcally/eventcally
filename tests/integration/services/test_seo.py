from project.services import seo


def _patch_paths(mocker, tmp_path):
    mocker.patch.object(seo, "cache_path", str(tmp_path))
    mocker.patch.object(seo, "robots_txt_path", str(tmp_path / "robots.txt"))
    mocker.patch.object(seo, "sitemap_path", str(tmp_path / "sitemap.xml"))


def test_generate_robots_txt_without_sitemap(app, mocker, tmp_path):
    _patch_paths(mocker, tmp_path)

    with app.test_request_context():
        seo.generate_robots_txt()

    lines = (tmp_path / "robots.txt").read_text().splitlines()
    assert lines == [
        "user-agent: *",
        "Disallow: /",
        "Allow: /eventdates",
        "Allow: /eventdate/",
        "Allow: /event/",
        "Allow: /calendars/",
    ]


def test_generate_robots_txt_links_an_existing_sitemap(app, mocker, tmp_path):
    _patch_paths(mocker, tmp_path)
    (tmp_path / "sitemap.xml").write_text("<urlset/>")

    with app.test_request_context():
        seo.generate_robots_txt()

    lines = (tmp_path / "robots.txt").read_text().splitlines()
    assert lines[-1].startswith("Sitemap: ")
    assert lines[-1].endswith("/sitemap.xml")


def test_generate_sitemap_lists_public_calendars_and_events(
    app, seeder, mocker, tmp_path
):
    _patch_paths(mocker, tmp_path)
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    public = seeder.create_calendar(admin_unit_id, "Public")
    private = seeder.create_calendar(admin_unit_id, "Secret", private=True)

    with app.test_request_context():
        seo.generate_sitemap()

    sitemap = (tmp_path / "sitemap.xml").read_text()
    assert f"/event/{event_id}</loc>" in sitemap
    assert f"/calendars/{public}</loc>" in sitemap
    assert f"/calendars/{private}</loc>" not in sitemap
    assert "<lastmod>" in sitemap
