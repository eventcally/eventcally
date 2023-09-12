import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_event_dates(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("widget_event_dates", id=admin_unit_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "widget.css")
    assert "X-Frame-Options" not in response.headers

    event_url = utils.get_url("event_date", id=1)
    utils.assert_response_contains(response, event_url)

    draft_url = utils.get_url("event_date", id=2)
    utils.assert_response_contains_not(response, draft_url)

    url = utils.get_url("widget_event_dates", id=admin_unit_id, keyword="name")
    utils.get_ok(url)

    url = utils.get_url("widget_event_dates", id=admin_unit_id, category_id=1)
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        coordinate="51.9077888,10.4333312",
        distance=500,
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        date_from="2020-10-03",
        date_to="2021-10-03",
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        s_ft="Verdana",
        s_bg="#eceef0",
        s_pr="#b09641",
        s_li="#7b2424",
    )
    utils.get_ok(url)

    # Unverified
    _, unverified_admin_unit_id, unverified_id = seeder.create_event_unverified()
    url = utils.get_url("widget_event_dates", id=unverified_admin_unit_id)
    response = utils.get_ok(url)

    unverified_date_id = seeder.get_event_date_id(unverified_id)
    unverified_url = utils.get_url("event_date", id=unverified_date_id)
    utils.assert_response_contains_not(response, unverified_url)


def test_event_dates_oneDay(client, seeder, utils):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base()

    start = create_berlin_date(2020, 10, 3, 10)
    end = create_berlin_date(2020, 10, 3, 11)
    name = "Spezialveranstaltung"
    seeder.create_event(admin_unit_id, name=name, start=start, end=end)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        date_from="2020-10-03",
        date_to="2020-10-03",
    )
    response = utils.get_ok(url)
    utils.assert_response_contains(response, name)


def test_event_dates_noneDescription(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, description=None)

    url = utils.get_url("widget_event_dates", id=admin_unit_id)
    utils.get_ok(url)


def get_create_data():
    return {
        "accept_tos": "y",
        "name": "Vorschlag",
        "start": ["2030-12-31", "23:59"],
        "contact_name": "Vorname Nachname",
        "contact_email": "vorname@nachname.de",
        "contact_email_notice": "y",
        "event_place_id": "Freitext Ort",
        "organizer_id": "Freitext Organisator",
    }


def test_event_dates_colors(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)

    with app.app_context():
        from colour import Color

        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.widget_font = "Verdana"
        admin_unit.widget_background_color = Color("#eceef0")
        admin_unit.widget_primary_color = Color("#b09641")
        admin_unit.widget_link_color = Color("#7b2424")
        db.session.commit()

    url = utils.get_url("widget_event_dates", id=admin_unit_id)
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("free_text", [True, False])
@pytest.mark.parametrize("free_text_suffix", [True, False])
@pytest.mark.parametrize("missing_preview_field", [True, False])
def test_event_suggestion_create_for_admin_unit(
    client,
    app,
    seeder,
    utils,
    mocker,
    db_error,
    free_text,
    free_text_suffix,
    missing_preview_field,
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("event_suggestion_create_for_admin_unit", id=admin_unit_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "widget.css")

    data = get_create_data()
    if not free_text:
        data["event_place_id"] = seeder.upsert_default_event_place(admin_unit_id)
        data["organizer_id"] = seeder.upsert_default_event_organizer(admin_unit_id)

    elif free_text_suffix:
        data["event_place_id_suffix"] = "Place address"
        data["organizer_id_suffix"] = "Organizer address"

    if db_error:
        utils.mock_db_commit(mocker)

    mail_mock = utils.mock_send_mails_async(mocker)

    if missing_preview_field:
        del data["accept_tos"]

    # preview post
    preview_response = utils.post_form(
        url + "?preview=True",
        response,
        data,
    )

    if missing_preview_field:
        utils.assert_response_error_message(preview_response)
        return

    utils.assert_response_ok(preview_response)

    # real post
    response = utils.post_form(
        url,
        response,
        data,
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    with app.app_context():
        from project.models import EventReviewStatus, EventSuggestion

        suggestion = (
            EventSuggestion.query.filter(EventSuggestion.admin_unit_id == admin_unit_id)
            .filter(EventSuggestion.name == "Vorschlag")
            .first()
        )
        assert suggestion is not None
        assert suggestion.review_status == EventReviewStatus.inbox
        suggestion_id = suggestion.id

    utils.assert_response_redirect(
        response, "event_suggestion_review_status", event_suggestion_id=suggestion_id
    )
    utils.assert_send_mail_called(mail_mock, "test@test.de")


def test_event_suggestion_create_for_admin_unit_allday(
    client,
    app,
    seeder,
    utils,
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("event_suggestion_create_for_admin_unit", id=admin_unit_id)
    response = utils.get_ok(url)

    data = get_create_data()
    data["allday"] = "y"
    response = utils.post_form(
        url,
        response,
        data,
    )

    with app.app_context():
        from project.models import EventSuggestion

        suggestion = (
            EventSuggestion.query.filter(EventSuggestion.admin_unit_id == admin_unit_id)
            .filter(EventSuggestion.name == "Vorschlag")
            .first()
        )
        assert suggestion is not None
        assert suggestion.allday
        suggestion_id = suggestion.id

    utils.assert_response_redirect(
        response, "event_suggestion_review_status", event_suggestion_id=suggestion_id
    )


def test_event_suggestion_create_for_admin_unit_startAfterEnd(
    client, app, seeder: Seeder, utils: UtilActions, mocker
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("event_suggestion_create_for_admin_unit", id=admin_unit_id)
    response = utils.get_ok(url)

    data = get_create_data()
    data["end"] = ["2030-12-31", "23:58"]

    response = utils.post_form(
        url,
        response,
        data,
    )
    utils.assert_response_error_message(
        response,
        "Der Start muss vor dem Ende sein",
    )


def test_event_suggestion_create_for_admin_unit_emptyFreeText(
    client, app, seeder, utils, mocker
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("event_suggestion_create_for_admin_unit", id=admin_unit_id)
    response = utils.get_ok(url)

    data = get_create_data()
    data["event_place_id"] = " "
    data["organizer_id"] = " "

    response = utils.post_form(
        url,
        response,
        data,
    )
    utils.assert_response_error_message(response)


def test_event_suggestion_create_for_admin_unit_invalidEventPlaceId(
    client, app, seeder, utils, mocker
):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("event_suggestion_create_for_admin_unit", id=admin_unit_id)
    response = utils.get_ok(url)

    data = get_create_data()
    data["event_place_id"] = "\u00B2"  # unicode for ²

    response = utils.post_form(
        url,
        response,
        data,
    )
    assert response.status_code == 302


def test_event_suggestion_create_for_admin_unit_notEnabled(client, app, seeder, utils):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(
        user_id, "Meine Crew", suggestions_enabled=False
    )

    url = utils.get_url("event_suggestion_create_for_admin_unit", id=admin_unit_id)
    response = utils.get(url)
    utils.assert_response_notFound(response)
