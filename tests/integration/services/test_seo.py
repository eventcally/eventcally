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
    ]


def test_generate_robots_txt_links_an_existing_sitemap(app, mocker, tmp_path):
    _patch_paths(mocker, tmp_path)
    (tmp_path / "sitemap.xml").write_text("<urlset/>")

    with app.test_request_context():
        seo.generate_robots_txt()

    lines = (tmp_path / "robots.txt").read_text().splitlines()
    assert lines[-1].startswith("Sitemap: ")
    assert lines[-1].endswith("/sitemap.xml")
