import datetime

import pytest

BASE_URL = "/bff/manage/organizations/{}"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/event/create")


def _flashes(client):
    with client.session_transaction() as session:
        return [
            (category, str(message))
            for category, message in session.get("_flashes", [])
        ]


def _urls(admin_unit_id, event_id=0):
    base = BASE_URL.format(admin_unit_id)
    return dict(
        create_form=f"{base}/events/create-form",
        form=f"{base}/events/{event_id}/form",
        events=f"{base}/events",
        event=f"{base}/events/{event_id}",
        occurrences=f"{base}/events/occurrences",
        custom_categories=f"{base}/custom-event-categories",
    )


def _body(seeder, admin_unit_id, **values):
    body = dict(
        name="Neue Veranstaltung",
        description="Beschreibung",
        date_definitions=[dict(start="2030-12-31T23:59")],
        organizer_id=seeder.upsert_default_event_organizer(admin_unit_id),
        event_place_id=seeder.upsert_default_event_place(admin_unit_id),
        category_ids=[seeder.get_event_category_id("Other")],
    )
    body.update(values)
    return body


def _photo(seeder, **values):
    photo = dict(
        image_base64=seeder.get_default_image_upload_base64(),
        copyright_text="EventCally",
        license_id=None,
    )
    photo.update(values)
    return photo


def _event(app, event_id):
    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import Event
        from project.shared.dateutils import berlin_tz

        event = db.session.get(Event, event_id)
        return dict(
            name=event.name,
            description=event.description,
            status=event.status,
            public_status=event.public_status,
            organizer_id=event.organizer_id,
            event_place_id=event.event_place_id,
            co_organizer_ids=sorted(o.id for o in event.co_organizers),
            category_ids=sorted(c.id for c in event.categories),
            custom_category_ids=sorted(c.id for c in event.custom_categories),
            tags=event.tags,
            internal_tags=event.internal_tags,
            kid_friendly=event.kid_friendly,
            age_from=event.age_from,
            rating=event.rating,
            target_group_origin=event.target_group_origin,
            attendance_mode=event.attendance_mode,
            photo=event.photo
            and (event.photo.data is not None, event.photo.copyright_text),
            date_definitions=[
                (
                    d.start.astimezone(berlin_tz),
                    d.end.astimezone(berlin_tz) if d.end else None,
                    d.allday,
                    d.recurrence_rule,
                )
                for d in event.date_definitions
            ],
        )


def _find_event(app, admin_unit_id, name):
    with app.app_context():
        from project.infrastructure.models import Event

        event = Event.query.filter(
            Event.admin_unit_id == admin_unit_id, Event.name == name
        ).first()
        return event and event.id


@pytest.fixture
def setup(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    _shell(utils, admin_unit_id)
    return admin_unit_id, event_id


def _other_organization(seeder, verified=True):
    other_user_id = seeder.create_user("other@test.de")
    return seeder.create_admin_unit(other_user_id, "Other Crew", verified=verified)


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    urls = _urls(admin_unit_id, 1)

    for call in (
        lambda: utils.get_json(urls["create_form"]),
        lambda: utils.get_json(urls["form"]),
        lambda: utils.post_json(urls["events"], {}),
        lambda: utils.put_json(urls["event"], {}),
        lambda: utils.post_json(urls["occurrences"], {}),
        lambda: utils.get_json(urls["custom_categories"] + "?set_id=1"),
    ):
        assert call().status_code == 401


def test_member_without_event_write_is_403(client, seeder, utils):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    event_id = seeder.create_event(admin_unit_id)
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()
    # Any Vue 3 shell carries the CSRF token for the writes.
    utils.get_ok("/organizations")
    urls = _urls(admin_unit_id, event_id)
    body = _body(seeder, admin_unit_id)

    assert utils.get_json(urls["create_form"]).status_code == 403
    assert utils.get_json(urls["form"]).status_code == 403
    assert utils.post_json(urls["events"], body).status_code == 403
    assert utils.put_json(urls["event"], body).status_code == 403
    occurrences = dict(start="2030-12-31T00:00", rrule="RRULE:FREQ=DAILY;COUNT=2")
    assert utils.post_json(urls["occurrences"], occurrences).status_code == 403
    lookup = urls["custom_categories"] + "?set_id=1"
    assert utils.get_json(lookup).status_code == 403


def test_foreign_organization_is_403(client, seeder, utils, setup):
    other_id = _other_organization(seeder)
    urls = _urls(other_id)

    assert utils.get_json(urls["create_form"]).status_code == 403
    body = _body(seeder, other_id)
    assert utils.post_json(urls["events"], body).status_code == 403


def test_event_of_another_organization_is_404(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = _other_organization(seeder)
    other_event_id = seeder.create_event(other_id, name="Fremd")
    urls = _urls(admin_unit_id, other_event_id)

    assert utils.get_json(urls["form"]).status_code == 404
    body = _body(seeder, admin_unit_id)
    assert utils.put_json(urls["event"], body).status_code == 404
    assert _event(app, other_event_id)["name"] == "Fremd"


def test_unknown_event_is_404(client, utils, setup):
    admin_unit_id, _ = setup

    assert utils.get_json(_urls(admin_unit_id, 4711)["form"]).status_code == 404


def test_unknown_template_is_404(client, utils, setup):
    admin_unit_id, _ = setup
    url = _urls(admin_unit_id)["create_form"] + "?template_id=4711"

    assert utils.get_json(url).status_code == 404


def test_unreadable_template_is_403(client, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = _other_organization(seeder)
    draft_id = seeder.create_event(other_id, draft=True)
    url = _urls(admin_unit_id)["create_form"] + f"?template_id={draft_id}"

    assert utils.get_json(url).status_code == 403


def test_write_requires_csrf(client, seeder):
    _, admin_unit_id = seeder.setup_base()

    response = client.post(_urls(admin_unit_id)["events"], json={})
    assert response.status_code == 400


# forms


def test_get_create_form_defaults(client, seeder, utils, setup, mocker):
    from project.shared.dateutils import berlin_tz

    admin_unit_id, _ = setup
    mocker.patch(
        "project.presentation.bff.manage.event_forms.get_next_full_hour",
        return_value=datetime.datetime(2030, 7, 1, 14, 0, tzinfo=berlin_tz),
    )

    body = utils.get_json_ok(_urls(admin_unit_id)["create_form"]).json

    assert body["id"] is None
    assert body["name"] == ""
    assert body["date_definitions"] == [
        dict(start="2030-07-01T14:00:00", end=None, allday=False, recurrence_rule=None)
    ]
    assert body["category_ids"] == [seeder.get_event_category_id("Other")]
    assert {c["id"] for c in body["category_choices"]} >= set(body["category_ids"])
    assert body["organizer"] is None
    assert body["event_place"] is None
    assert body["photo"] is None
    assert body["status"] is None
    assert body["status_choices"] == []
    assert body["public_status"] == 2
    assert body["target_group_origin"] == 1
    assert [c["value"] for c in body["target_group_origin_choices"]] == [1, 2, 3]
    assert body["attendance_mode"] == 1
    assert [c["value"] for c in body["attendance_mode_choices"]] == [1, 2, 3]
    assert body["rating"] == 50
    assert len(body["rating_choices"]) == 11
    assert body["can_create_place"] is True
    assert body["can_create_organizer"] is True
    assert body["custom_category_sets"]
    assert all(s["selected"] == [] for s in body["custom_category_sets"])
    # Meine Crew is verified: the eventcally organization is suggested.
    eventcally_id = seeder.get_eventcally_admin_unit_id()
    assert eventcally_id in [c["id"] for c in body["reference_request_choices"]]


def test_get_create_form_without_default_category(
    client, app, db, seeder, utils, setup
):
    admin_unit_id, _ = setup
    other_category_id = seeder.get_event_category_id("Other")

    with app.app_context():
        from project.infrastructure.models import EventCategory

        category = db.session.get(EventCategory, other_category_id)
        category.name = "Renamed"
        db.session.commit()

    body = utils.get_json_ok(_urls(admin_unit_id)["create_form"]).json

    assert body["category_ids"] == []


def test_get_create_form_unverified_has_no_reference_requests(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(admin_unit_verified=False)

    body = utils.get_json_ok(_urls(admin_unit_id)["create_form"]).json

    assert body["reference_request_choices"] == []
    assert body["reference_request_ids"] == []


def test_get_create_form_from_own_template(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mitveranstalter")
    _, custom_category_id = seeder.get_one_custom_event_category_set()
    template_id = seeder.create_event(
        admin_unit_id,
        name="Vorlage",
        tags="a,b",
        internal_tags="intern",
        co_organizer_ids=[organizer_id],
        custom_category_ids=[custom_category_id],
        recurrence_rule="RRULE:FREQ=DAILY;COUNT=7",
        rating=80,
        kid_friendly=True,
        age_from=6,
    )
    seeder.assign_image_to_event(template_id, seeder.upsert_default_image())
    url = _urls(admin_unit_id)["create_form"] + f"?template_id={template_id}"

    body = utils.get_json_ok(url).json

    assert body["id"] is None
    assert body["name"] == "Vorlage"
    assert body["tags"] == "a,b"
    assert body["internal_tags"] == "intern"
    assert body["rating"] == 80
    assert body["kid_friendly"] is True
    assert body["age_from"] == 6
    assert body["organizer"]["id"] == seeder.upsert_default_event_organizer(
        admin_unit_id
    )
    assert body["event_place"]["name"].startswith("Meine Crew")
    assert body["co_organizers"] == [dict(id=organizer_id, name="Mitveranstalter")]
    assert body["date_definitions"][0]["recurrence_rule"] == "RRULE:FREQ=DAILY;COUNT=7"
    assert body["photo"]["image_base64"].startswith("data:image/")
    selected = [c["id"] for s in body["custom_category_sets"] for c in s["selected"]]
    assert selected == [custom_category_id]


def test_get_create_form_from_foreign_template(client, seeder, utils, setup):
    admin_unit_id, _ = setup
    other_id = _other_organization(seeder)
    template_id = seeder.create_event(
        other_id, name="Fremde Vorlage", internal_tags="geheim", rating=90
    )
    url = _urls(admin_unit_id)["create_form"] + f"?template_id={template_id}"

    body = utils.get_json_ok(url).json

    assert body["name"] == "Fremde Vorlage"
    assert body["organizer"] is None
    assert body["event_place"] is None
    assert body["co_organizers"] == []
    assert body["internal_tags"] is None
    assert body["rating"] == 50


def test_get_form_prefills_all_fields(client, app, seeder, utils, setup):
    from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
    from project.domain.models.enums.event_public_status import EventPublicStatus
    from project.domain.models.enums.event_status import EventStatus
    from project.domain.models.enums.event_target_group_origin import (
        EventTargetGroupOrigin,
    )
    from project.shared.dateutils import berlin_tz

    admin_unit_id, _ = setup
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mitveranstalter")
    _, custom_category_id = seeder.get_one_custom_event_category_set()
    event_id = seeder.create_event(
        admin_unit_id,
        name="Stadtfest",
        start=datetime.datetime(2030, 7, 1, 14, 0, tzinfo=berlin_tz),
        end=datetime.datetime(2030, 7, 1, 18, 30, tzinfo=berlin_tz),
        recurrence_rule="RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6",
        co_organizer_ids=[organizer_id],
        custom_category_ids=[custom_category_id],
        internal_tags="intern",
        status=EventStatus.cancelled,
        public_status=EventPublicStatus.planned,
        target_group_origin=EventTargetGroupOrigin.tourist,
    )
    seeder.assign_image_to_event(event_id, seeder.upsert_default_image())

    body = utils.get_json_ok(_urls(admin_unit_id, event_id)["form"]).json

    assert body["id"] == event_id
    assert body["name"] == "Stadtfest"
    assert body["date_definitions"] == [
        dict(
            start="2030-07-01T14:00:00",
            end="2030-07-01T18:30:00",
            allday=False,
            recurrence_rule="RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6",
        )
    ]
    assert body["status"] == 2
    assert body["public_status"] == 3
    assert [c["value"] for c in body["status_choices"]] == [1, 2, 3, 4, 5]
    assert [c["value"] for c in body["public_status_choices"]] == [2, 3, 1]
    assert body["target_group_origin"] == 2
    # The seeder always creates offline events.
    assert body["attendance_mode"] == int(EventAttendanceMode.offline)
    assert body["co_organizers"] == [dict(id=organizer_id, name="Mitveranstalter")]
    assert body["internal_tags"] == "intern"
    assert body["photo"]["copyright_text"]
    assert body["reference_request_choices"] == []
    selected = [c["id"] for s in body["custom_category_sets"] for c in s["selected"]]
    assert selected == [custom_category_id]


# create


@pytest.mark.parametrize(
    "public_status, flash_text",
    [
        (2, "Veranstaltung erfolgreich veröffentlicht"),
        (3, "Veranstaltung erfolgreich geplant"),
        (1, "Entwurf erfolgreich gespeichert"),
    ],
)
def test_create(client, app, seeder, utils, setup, public_status, flash_text):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(seeder, admin_unit_id, public_status=public_status),
    )

    assert response.status_code == 201
    event_id = _find_event(app, admin_unit_id, "Neue Veranstaltung")
    assert response.json == dict(
        id=event_id,
        redirect_url=utils.get_url("main.event_actions", event_id=event_id),
    )
    event = _event(app, event_id)
    assert event["public_status"] == public_status
    assert event["description"] == "Beschreibung"
    start = event["date_definitions"][0][0]
    assert (start.year, start.month, start.day, start.hour, start.minute) == (
        2030,
        12,
        31,
        23,
        59,
    )
    flashes = _flashes(client)
    assert flashes[0][0] == "success"
    assert flashes[0][1].startswith(flash_text)
    show_url = utils.get_url("main.event", event_id=event_id)
    assert f'<a href="{show_url}">Anzeigen</a>' in flashes[0][1]
    assert len(flashes) == 1


def test_create_all_fields(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mitveranstalter")
    _, custom_category_id = seeder.get_one_custom_event_category_set()

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            date_definitions=[
                dict(
                    start="2030-12-30T10:00",
                    end="2030-12-30T12:00",
                    recurrence_rule="RRULE:FREQ=DAILY;COUNT=3",
                ),
                dict(start="2030-12-31T00:00", end="", allday=True),
            ],
            co_organizer_ids=[organizer_id],
            custom_category_ids=[custom_category_id],
            tags="a,b",
            internal_tags="",
            kid_friendly=True,
            age_from=6,
            rating=80,
            target_group_origin=3,
            attendance_mode=2,
            photo=_photo(seeder),
        ),
    )

    assert response.status_code == 201
    event = _event(app, response.json["id"])
    assert event["co_organizer_ids"] == [organizer_id]
    assert event["custom_category_ids"] == [custom_category_id]
    assert event["tags"] == "a,b"
    assert event["internal_tags"] is None
    assert event["kid_friendly"] is True
    assert event["age_from"] == 6
    assert event["rating"] == 80
    assert int(event["target_group_origin"]) == 3
    assert int(event["attendance_mode"]) == 2
    assert event["photo"] == (True, "EventCally")
    assert len(event["date_definitions"]) == 2
    assert event["date_definitions"][0][3] == "RRULE:FREQ=DAILY;COUNT=3"
    assert event["date_definitions"][1][2] is True


def test_create_with_reference_requests(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    eventcally_admin_unit_id = seeder.get_eventcally_admin_unit_id()
    other_admin_unit_id = _other_organization(seeder)
    seeder.create_admin_unit_relation(
        other_admin_unit_id, admin_unit_id, auto_verify_event_reference_requests=True
    )

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            reference_request_ids=[eventcally_admin_unit_id, other_admin_unit_id],
        ),
    )

    assert response.status_code == 201
    event_id = response.json["id"]

    with app.app_context():
        from project.infrastructure.models import (
            EventReference,
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        def request_status(target_id):
            return (
                EventReferenceRequest.query.filter(
                    EventReferenceRequest.admin_unit_id == target_id,
                    EventReferenceRequest.event_id == event_id,
                )
                .one()
                .review_status
            )

        assert (
            request_status(eventcally_admin_unit_id)
            == EventReferenceRequestReviewStatus.inbox
        )
        assert (
            request_status(other_admin_unit_id)
            == EventReferenceRequestReviewStatus.verified
        )
        assert EventReference.query.filter(
            EventReference.admin_unit_id == other_admin_unit_id,
            EventReference.event_id == event_id,
        ).first()

    assert len(_flashes(client)) == 3


def test_create_draft_skips_reference_requests(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup
    eventcally_admin_unit_id = seeder.get_eventcally_admin_unit_id()

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            public_status=1,
            reference_request_ids=[eventcally_admin_unit_id],
        ),
    )

    assert response.status_code == 201

    with app.app_context():
        from project.infrastructure.models import EventReferenceRequest

        assert EventReferenceRequest.query.count() == 0

    assert len(_flashes(client)) == 1


def test_create_reference_request_outside_suggestions_is_422(
    client, seeder, utils, setup
):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(seeder, admin_unit_id, reference_request_ids=[4711]),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["reference_request_ids"]


def _error_locs(response):
    return [error["loc"] for error in response.json["errors"]]


def test_create_place_and_organizer_of_another_organization_is_422(
    client, app, seeder, utils, setup
):
    admin_unit_id, _ = setup
    other_id = _other_organization(seeder)

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            organizer_id=seeder.upsert_default_event_organizer(other_id),
            event_place_id=seeder.upsert_default_event_place(other_id),
            co_organizer_ids=[seeder.upsert_event_organizer(other_id, "Fremd")],
        ),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [
        ["organizer_id"],
        ["event_place_id"],
        ["co_organizer_ids"],
    ]
    assert _find_event(app, admin_unit_id, "Neue Veranstaltung") is None


def test_create_missing_fields_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            organizer_id=None,
            event_place_id=None,
            category_ids=[],
        ),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [
        ["organizer_id"],
        ["event_place_id"],
        ["category_ids"],
    ]
    assert response.json["errors"][0]["msg"] == "Dieses Feld ist erforderlich."


def test_create_unknown_categories_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(seeder, admin_unit_id, category_ids=[4711], custom_category_ids=[4711]),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [["category_ids"], ["custom_category_ids"]]


def test_create_invalid_photo_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(seeder, admin_unit_id, photo=_photo(seeder, copyright_text="")),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [["photo", "copyright_text"]]


def test_create_without_date_definitions_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(seeder, admin_unit_id, date_definitions=[]),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [["date_definitions"]]


# dates (ported from the legacy form tests)


def test_create_start_after_end_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            date_definitions=[
                dict(start="2030-12-31T00:00"),
                dict(start="2030-12-31T00:00", end="2030-12-30T23:59"),
            ],
        ),
    )

    assert response.status_code == 422
    assert response.json["errors"] == [
        dict(
            loc=["date_definitions", "1", "start"],
            msg="Der Start muss vor dem Ende sein.",
        )
    ]


def test_create_duration_more_than_180_days_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            date_definitions=[dict(start="2030-12-31T00:00", end="2031-06-29T12:01")],
        ),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["date_definitions", "0", "end"]
    assert "180 Tage" in response.json["errors"][0]["msg"]


def test_create_allday_180_day_cap_counts_berlin_wall_clock_across_dst(
    client, app, seeder, utils, setup
):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            date_definitions=[
                dict(start="2030-06-01T00:00", end="2030-11-27T23:59", allday=True)
            ],
        ),
    )

    assert response.status_code == 201
    end = _event(app, response.json["id"])["date_definitions"][0][1]
    assert end.date() == datetime.date(2030, 11, 27)
    assert (end.hour, end.minute, end.second) == (23, 59, 59)
    assert end.utcoffset() == datetime.timedelta(hours=1)


def test_create_allday_181_day_span_across_dst_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            date_definitions=[
                dict(start="2030-06-01T00:00", end="2030-11-28T00:00", allday=True)
            ],
        ),
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["date_definitions", "0", "end"]


def test_create_accepts_aware_dates(client, app, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"],
        _body(
            seeder,
            admin_unit_id,
            date_definitions=[dict(start="2030-12-31T22:59:00+00:00")],
        ),
    )

    assert response.status_code == 201
    start = _event(app, response.json["id"])["date_definitions"][0][0]
    assert (start.hour, start.minute) == (23, 59)


# update


def test_update(client, app, seeder, utils, setup):
    from project.domain.events.event_updated import EventUpdated

    admin_unit_id, event_id = setup
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mitveranstalter")

    response = utils.put_json(
        _urls(admin_unit_id, event_id)["event"],
        _body(
            seeder,
            admin_unit_id,
            name="Neuer Name",
            status=2,
            public_status=3,
            co_organizer_ids=[organizer_id],
            date_definitions=[
                dict(start="2030-12-31T14:00"),
                dict(start="2031-01-31T14:00"),
            ],
        ),
    )

    assert response.status_code == 200
    assert response.json == dict(
        id=event_id,
        redirect_url=utils.get_url("manage_admin_unit.events", id=admin_unit_id),
    )
    event = _event(app, event_id)
    assert event["name"] == "Neuer Name"
    assert int(event["status"]) == 2
    assert int(event["public_status"]) == 3
    assert event["co_organizer_ids"] == [organizer_id]
    assert len(event["date_definitions"]) == 2
    assert _flashes(client) == [("success", "Veranstaltung erfolgreich aktualisiert")]

    with app.app_context():
        event_updated = app.test_event_dispatcher.get_first_event_by_type(EventUpdated)
        assert event_updated is not None


def test_update_photo_keep_replace_remove(client, app, seeder, utils, setup):
    admin_unit_id, event_id = setup
    seeder.assign_image_to_event(event_id, seeder.upsert_default_image())
    url = _urls(admin_unit_id, event_id)["event"]

    keep = dict(image_base64=None, copyright_text="Neu", license_id=None)
    assert (
        utils.put_json(url, _body(seeder, admin_unit_id, photo=keep)).status_code == 200
    )
    assert _event(app, event_id)["photo"] == (True, "Neu")

    replace = _photo(seeder, copyright_text="Ersetzt")
    assert (
        utils.put_json(url, _body(seeder, admin_unit_id, photo=replace)).status_code
        == 200
    )
    assert _event(app, event_id)["photo"] == (True, "Ersetzt")

    assert (
        utils.put_json(url, _body(seeder, admin_unit_id, photo=None)).status_code == 200
    )
    assert _event(app, event_id)["photo"] is None


def test_update_validation_is_422(client, app, seeder, utils, setup):
    admin_unit_id, event_id = setup

    response = utils.put_json(
        _urls(admin_unit_id, event_id)["event"],
        _body(seeder, admin_unit_id, name="Neu", category_ids=[]),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [["category_ids"]]
    assert _event(app, event_id)["name"] == "Name"


# occurrences and lookups


def test_occurrences(client, utils, setup):
    admin_unit_id, _ = setup
    url = _urls(admin_unit_id)["occurrences"]

    response = utils.post_json(
        url,
        dict(
            start="2030-12-30T14:00",
            rrule="RRULE:FREQ=DAILY;COUNT=12\nEXDATE:20301231T000000",
        ),
    )

    assert response.status_code == 200
    items = response.json["items"]
    assert items[0] == dict(
        date="20301230T000000", formatted_date="30.12.2030", type="start"
    )
    assert items[1]["type"] == "exdate"
    assert response.json["has_more"] is True

    response = utils.post_json(
        url,
        dict(
            start="2030-12-30T14:00",
            rrule="RRULE:FREQ=DAILY;COUNT=12\nEXDATE:20301231T000000",
            batch_start=10,
        ),
    )

    assert response.status_code == 200
    assert [i["type"] for i in response.json["items"]] == ["rrule", "rrule"]
    assert response.json["has_more"] is False


def test_occurrences_bad_rule_is_422(client, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["occurrences"],
        dict(start="2030-12-30T14:00", rrule="RRULE:FREQ=NOPE"),
    )

    assert response.status_code == 422
    assert _error_locs(response) == [["rrule"]]


def test_lookup_custom_event_categories(client, seeder, utils, setup):
    admin_unit_id, _ = setup
    set_id, category_id = seeder.get_one_custom_event_category_set()
    url = _urls(admin_unit_id)["custom_categories"]

    body = utils.get_json_ok(f"{url}?set_id={set_id}").json
    assert category_id in [c["id"] for c in body["items"]]

    body = utils.get_json_ok(f"{url}?set_id=4711").json
    assert body["items"] == []


def test_create_unknown_rating_is_422(client, seeder, utils, setup):
    admin_unit_id, _ = setup

    response = utils.post_json(
        _urls(admin_unit_id)["events"], _body(seeder, admin_unit_id, rating=55)
    )

    assert response.status_code == 422
    assert _error_locs(response) == [["rating"]]


# referenced event change notices


def _form_to_body(form, **values):
    """The PUT body the Vue form sends for the values its GET returned."""
    body = dict(
        name=form["name"],
        description=form["description"],
        date_definitions=form["date_definitions"],
        status=form["status"],
        public_status=form["public_status"],
        organizer_id=form["organizer"]["id"],
        event_place_id=form["event_place"]["id"],
        co_organizer_ids=[o["id"] for o in form["co_organizers"]],
        category_ids=form["category_ids"],
        custom_category_ids=[
            c["id"] for s in form["custom_category_sets"] for c in s["selected"]
        ],
        photo=form["photo"],
        external_link=form["external_link"],
        ticket_link=form["ticket_link"],
        tags=form["tags"],
        internal_tags=form["internal_tags"],
        kid_friendly=form["kid_friendly"],
        accessible_for_free=form["accessible_for_free"],
        registration_required=form["registration_required"],
        booked_up=form["booked_up"],
        age_from=form["age_from"],
        age_to=form["age_to"],
        expected_participants=form["expected_participants"],
        price_info=form["price_info"],
        target_group_origin=form["target_group_origin"],
        attendance_mode=form["attendance_mode"],
        rating=form["rating"],
    )
    body.update(values)
    return body


def _referenced_event(client, app, seeder, utils, **values):
    """An event of "Other Crew", created through the form and referenced by the
    first organization. Returns the other organization's id and the event id."""
    _, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = _other_organization(seeder)

    utils.logout()
    utils.login("other@test.de")
    _shell(utils, other_admin_unit_id)

    response = utils.post_json(
        _urls(other_admin_unit_id)["events"],
        _body(
            seeder,
            other_admin_unit_id,
            name="Name",
            photo=_photo(seeder),
            **values,
        ),
    )
    assert response.status_code == 201
    event_id = response.json["id"]
    seeder.create_reference(event_id, admin_unit_id)
    return other_admin_unit_id, event_id


def _put_form(utils, admin_unit_id, event_id, **values):
    urls = _urls(admin_unit_id, event_id)
    form = utils.get_json_ok(urls["form"]).json
    response = utils.put_json(urls["event"], _form_to_body(form, **values))
    assert response.status_code == 200
    return form


def _handle_pending_events(app):
    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()


def test_referenced_event_update_sends_mail(client, app, seeder, utils):
    admin_unit_id, event_id = _referenced_event(client, app, seeder, utils)

    _put_form(utils, admin_unit_id, event_id, name="Changed name")
    _handle_pending_events(app)

    assert (
        app.test_email_service.sent_emails[0]["subject"]
        == "Empfohlene Veranstaltung wurde geändert"
    )
    assert app.test_email_service.sent_emails[0]["recipient"] == "test@test.de"


def test_referenced_event_non_dirty_update_does_not_send_mail(
    client, app, seeder, utils
):
    admin_unit_id, event_id = _referenced_event(client, app, seeder, utils)

    _put_form(utils, admin_unit_id, event_id)
    _handle_pending_events(app)

    assert len(app.test_email_service.sent_emails) == 0


def test_referenced_allday_event_non_dirty_update_does_not_send_mail(
    client, app, seeder, utils
):
    """An all-day end is stored as 23:59:59, but the form's wall-clock input
    (`YYYY-MM-DDTHH:MM`) has no seconds. Unless the value object widens it back,
    an untouched all-day event looks changed and sends a notice whose old and
    new dates render identically."""
    admin_unit_id, event_id = _referenced_event(
        client,
        app,
        seeder,
        utils,
        date_definitions=[dict(start="2030-12-31T00:00", allday=True)],
    )

    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import Event
        from project.shared.dateutils import berlin_tz

        date_definition = db.session.get(Event, event_id).date_definitions[0]
        # Without these the test degrades into a plain non-dirty update as soon
        # as the form stops producing an all-day event, and still passes.
        assert date_definition.allday
        assert date_definition.end.astimezone(berlin_tz) == datetime.datetime(
            2030, 12, 31, 23, 59, 59, tzinfo=berlin_tz
        )

    _put_form(utils, admin_unit_id, event_id)
    _handle_pending_events(app)

    assert len(app.test_email_service.sent_emails) == 0


def test_referenced_recurring_event_non_dirty_update_does_not_send_mail(
    client, app, seeder, utils
):
    # A recurring event re-posted unchanged sent a "referenced event changed"
    # mail whose old/new summary printed identically (the notice only renders
    # start + a "Recurring event" flag, never the recurrence_rule content).
    #
    # EventDateDefinitionValueObject equality is plain pydantic ``==``, which
    # is exact on strings, so ``recurrence_rule`` is normalized by the
    # ``NullableRecurrenceRule`` type. The recurrence editor appends an EXDATE
    # line with a bare "\n" once a single occurrence is excluded from a series,
    # e.g. "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260504". A browser normalizes
    # textarea line breaks to CRLF, so the same rule can come back with
    # different line endings, which compare unequal byte-for-byte.
    recurrence_rule_lf = "RRULE:FREQ=WEEKLY;COUNT=5\nEXDATE:20260504"
    admin_unit_id, event_id = _referenced_event(
        client,
        app,
        seeder,
        utils,
        date_definitions=[
            dict(start="2026-04-06T11:00", recurrence_rule=recurrence_rule_lf)
        ],
    )

    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import Event

        event = db.session.get(Event, event_id)
        assert event.date_definitions[0].recurrence_rule == recurrence_rule_lf

    recurrence_rule_crlf = recurrence_rule_lf.replace("\n", "\r\n")
    form = utils.get_json_ok(_urls(admin_unit_id, event_id)["form"]).json
    form["date_definitions"][0]["recurrence_rule"] = recurrence_rule_crlf
    response = utils.put_json(
        _urls(admin_unit_id, event_id)["event"], _form_to_body(form)
    )
    assert response.status_code == 200
    _handle_pending_events(app)

    assert len(app.test_email_service.sent_emails) == 0


def test_referenced_recurring_event_change_sends_mail_but_diff_is_indistinguishable(
    client, app, seeder, utils
):
    # Here the recurrence rule genuinely changes (fewer occurrences), so
    # sending a mail is correct. But the notice only ever renders
    # "(Recurring event)" for a recurring definition -- never the
    # recurrence_rule content -- so the "before"/"after" lines print
    # identically even though the event's actual occurrences changed.
    admin_unit_id, event_id = _referenced_event(
        client,
        app,
        seeder,
        utils,
        date_definitions=[
            dict(start="2026-04-06T11:00", recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=5")
        ],
    )

    urls = _urls(admin_unit_id, event_id)
    form = utils.get_json_ok(urls["form"]).json
    # A real change: five occurrences shrink to three.
    form["date_definitions"][0]["recurrence_rule"] = "RRULE:FREQ=WEEKLY;COUNT=3"
    response = utils.put_json(urls["event"], _form_to_body(form))
    assert response.status_code == 200
    _handle_pending_events(app)

    with app.app_context():
        from project.infrastructure.extensions import db
        from project.infrastructure.models import Event

        event = db.session.get(Event, event_id)
        assert event.date_definitions[0].recurrence_rule == "RRULE:FREQ=WEEKLY;COUNT=3"

    assert len(app.test_email_service.sent_emails) == 1
    body = app.test_email_service.sent_emails[0]["body"]

    old_section = body.split("Termine (bisher):")[1].split("Termine (neu):")[0]
    new_section = body.split("Termine (neu):")[1]
    old_line = old_section.strip().splitlines()[0].strip()
    new_line = new_section.strip().splitlines()[0].strip()

    # The mail correctly reports that something changed, but the rendered
    # lines are byte-identical: the recipient cannot tell what changed.
    assert old_line == new_line == "- 06.04.26 11:00 (Serientermin)"
