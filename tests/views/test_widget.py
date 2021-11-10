import pytest


def test_event_dates(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)
    au_short_name = "meinecrew"

    url = utils.get_url("widget_event_dates", au_short_name=au_short_name)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "widget.css")

    event_url = utils.get_url("widget_event_date", au_short_name=au_short_name, id=1)
    utils.assert_response_contains(response, event_url)

    draft_url = utils.get_url("widget_event_date", au_short_name=au_short_name, id=2)
    utils.assert_response_contains_not(response, draft_url)

    url = utils.get_url(
        "widget_event_dates", au_short_name=au_short_name, keyword="name"
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates", au_short_name=au_short_name, category_id=1
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        au_short_name=au_short_name,
        coordinate="51.9077888,10.4333312",
        distance=500,
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        au_short_name=au_short_name,
        date_from="2020-10-03",
        date_to="2021-10-03",
    )
    utils.get_ok(url)

    # Unverified
    au_short_name = "unverifiedcrew"
    _, _, unverified_id = seeder.create_event_unverified()
    url = utils.get_url("widget_event_dates", au_short_name=au_short_name)
    response = utils.get_ok(url)

    unverified_date_id = seeder.get_event_date_id(unverified_id)
    unverified_url = utils.get_url(
        "widget_event_date", au_short_name=au_short_name, id=unverified_date_id
    )
    utils.assert_response_contains_not(response, unverified_url)


def test_event_dates_oneDay(client, seeder, utils):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base()
    au_short_name = "meinecrew"

    start = create_berlin_date(2020, 10, 3, 10)
    end = create_berlin_date(2020, 10, 3, 11)
    name = "Spezialveranstaltung"
    seeder.create_event(admin_unit_id, name=name, start=start, end=end)

    url = utils.get_url(
        "widget_event_dates",
        au_short_name=au_short_name,
        date_from="2020-10-03",
        date_to="2020-10-03",
    )
    response = utils.get_ok(url)
    utils.assert_response_contains(response, name)


def test_event_date(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)
    au_short_name = "meinecrew"

    with app.app_context():
        from colour import Color

        from project.models import AdminUnit

        admin_unit = AdminUnit.query.get(admin_unit_id)
        admin_unit.widget_font = "Arial"
        admin_unit.widget_background_color = Color("#F5F5F5")
        admin_unit.widget_primary_color = Color("#000000")
        admin_unit.widget_link_color = Color("#FF0000")
        db.session.commit()

    url = utils.get_url("widget_event_date", au_short_name=au_short_name, id=1)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "widget.css")

    seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("widget_event_date", au_short_name=au_short_name, id=2)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    # Unverified
    au_short_name = "unverifiedcrew"
    _, _, unverified_id = seeder.create_event_unverified()
    unverified_date_id = seeder.get_event_date_id(unverified_id)
    url = utils.get_url(
        "widget_event_date", au_short_name=au_short_name, id=unverified_date_id
    )
    utils.assert_response_unauthorized(response)


def test_event_date_co_organizers(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )
    au_short_name = "meinecrew"

    url = utils.get_url("widget_event_date", au_short_name=au_short_name, id=event_id)
    response = utils.get(url)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "Organizer A")
    utils.assert_response_contains(response, "Organizer B")


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
    au_short_name = "meinecrew"

    url = utils.get_url(
        "event_suggestion_create_for_admin_unit", au_short_name=au_short_name
    )
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

    mail_mock = utils.mock_send_mails(mocker)

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
    au_short_name = "meinecrew"

    url = utils.get_url(
        "event_suggestion_create_for_admin_unit", au_short_name=au_short_name
    )
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
    client, app, seeder, utils, mocker
):
    user_id = seeder.create_user()
    seeder.create_admin_unit(user_id, "Meine Crew")
    au_short_name = "meinecrew"

    url = utils.get_url(
        "event_suggestion_create_for_admin_unit", au_short_name=au_short_name
    )
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
    seeder.create_admin_unit(user_id, "Meine Crew")
    au_short_name = "meinecrew"

    url = utils.get_url(
        "event_suggestion_create_for_admin_unit", au_short_name=au_short_name
    )
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
    seeder.create_admin_unit(user_id, "Meine Crew")
    au_short_name = "meinecrew"

    url = utils.get_url(
        "event_suggestion_create_for_admin_unit", au_short_name=au_short_name
    )
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
    seeder.create_admin_unit(user_id, "Meine Crew", suggestions_enabled=False)
    au_short_name = "meinecrew"

    url = utils.get_url(
        "event_suggestion_create_for_admin_unit", au_short_name=au_short_name
    )
    response = utils.get(url)
    utils.assert_response_notFound(response)
