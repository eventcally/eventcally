"""SqlAlchemySiteSettingsReadRepository against the database, on the read session."""

import pytest


@pytest.fixture
def notices(app, db):
    def call():
        with app.app_context():
            repo = app.container.read_repos.site_settings_read_repo()

            with app.container.infrastructure.read_session_scope():
                return repo.get_site_notices()

    return call


def _set(app, db, **values):
    with app.app_context():
        from project.init_data import upsert_settings

        settings = upsert_settings()
        for key, value in values.items():
            setattr(settings, key, value)
        db.session.commit()


@pytest.fixture
def settings(app, db):
    def call():
        with app.app_context():
            repo = app.container.read_repos.site_settings_read_repo()

            with app.container.infrastructure.read_session_scope():
                return repo.get_settings()

    return call


def test_no_settings_row_means_empty_settings(app, db, settings):
    result = settings()

    assert result.tos is None
    assert result.planning_external_calendars is None

    with app.app_context():
        from project.models import Settings

        assert db.session.query(Settings).count() == 0


def test_settings_values_are_read(app, db, settings):
    _set(
        app,
        db,
        tos="Terms",
        legal_notice="Legal",
        contact="Contact",
        privacy="Privacy",
        start_page="Start",
        announcement="News",
        planning_external_calendars='[{"url": "x"}]',
    )

    result = settings()

    assert result.model_dump() == {
        "tos": "Terms",
        "legal_notice": "Legal",
        "contact": "Contact",
        "privacy": "Privacy",
        "start_page": "Start",
        "announcement": "News",
        "planning_external_calendars": '[{"url": "x"}]',
    }


def test_no_settings_row_means_no_notices(notices):
    result = notices()

    assert result.has_tos is False
    assert result.announcement is None


def test_empty_strings_mean_no_notices(app, db, notices):
    _set(app, db, tos="", announcement="")

    result = notices()

    assert result.has_tos is False
    assert result.announcement is None


def test_values_are_read(app, db, notices):
    _set(app, db, tos="Terms", announcement="Wartungsarbeiten")

    result = notices()

    assert result.has_tos is True
    assert result.announcement == "Wartungsarbeiten"


def test_reading_never_inserts_a_settings_row(app, db, notices):
    notices()

    with app.app_context():
        from project.models import Settings

        assert db.session.query(Settings).count() == 0
