"""A deterministic event world shared by the event read parity tests.

Fixed timestamps and far-future dates keep API bodies, pages and iCal feeds stable.
Organization A ("Meine Crew", verified, API access) owns most events; B ("Other Crew",
verified) owns one that A references; C ("Unverified Crew") is not verified.
"""

from sqlalchemy import text

from project.dateutils import create_berlin_date

TRACKED_TABLES = [
    "adminunit",
    "event",
    "eventorganizer",
    "eventplace",
    "image",
    "eventreference",
    "eventdate",
]

LONG_DESCRIPTION = " ".join(f"Beschreibung {i}" for i in range(60))


def _normalize_timestamps(db):
    for table in TRACKED_TABLES:
        columns = {
            row[0]
            for row in db.session.execute(
                text(
                    "SELECT column_name FROM information_schema.columns"
                    " WHERE table_name = :table"
                ),
                {"table": table},
            )
        }
        assignments = []

        if "created_at" in columns:
            assignments.append(
                "created_at = timestamp '2026-01-01 08:00:00'"
                " + id * interval '1 day'"
            )

        if "updated_at" in columns:
            assignments.append(
                "updated_at = CASE WHEN id % 2 = 0 THEN timestamp"
                " '2026-02-01 09:30:00' + id * interval '1 hour' ELSE NULL END"
            )

        if assignments:
            db.session.execute(text(f"UPDATE {table} SET {', '.join(assignments)}"))

    db.session.commit()


def seed_event_world(app, db, seeder):
    from project.infrastructure.models import (
        CustomEventCategory,
        Event,
        EventCategory,
        EventOrganizer,
        EventPlace,
        EventReference,
        EventStatus,
        Location,
    )

    _, a_id = seeder.setup_api_access(admin=False)
    b_user_id = seeder.create_user("other@test.de")
    b_id = seeder.create_admin_unit(b_user_id, "Other Crew")
    seeder.verify_admin_unit(b_id)
    c_user_id = seeder.create_user("unverified@test.de")
    c_id = seeder.create_admin_unit(c_user_id, "Unverified Crew")

    organizer_one = seeder.upsert_event_organizer(a_id, "Organizer One")
    organizer_two = seeder.upsert_event_organizer(a_id, "Organizer Two")
    rathaus_id = seeder.upsert_event_place(
        a_id,
        "Rathaus",
        Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            state="Niedersachsen",
            country="DE",
            latitude="51.9077888",
            longitude="10.4333312",
        ),
    )
    online_id = seeder.upsert_event_place(a_id, "Online Raum")
    image_id = seeder.upsert_default_image()
    _, custom_category_id = seeder.get_one_custom_event_category_set()

    ids = {"a": a_id, "b": b_id, "c": c_id, "rathaus": rathaus_id}

    ids["full"] = seeder.create_event(
        a_id,
        name="Full Event",
        start=create_berlin_date(2040, 3, 1, 18),
        end=create_berlin_date(2040, 3, 1, 20),
        tags="music,live",
        internal_tags="secret,inhouse",
        place_id=rathaus_id,
        description=LONG_DESCRIPTION,
        external_link="https://example.com/full",
        co_organizer_ids=[organizer_one, organizer_two],
        custom_category_ids=[custom_category_id],
    )
    seeder.add_event_date_definition(
        ids["full"], start=create_berlin_date(2040, 3, 8, 18)
    )
    ids["recurring"] = seeder.create_event(
        a_id,
        name="Weekly Jam",
        start=create_berlin_date(2040, 4, 2, 19),
        recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=3",
        tags="music",
    )
    ids["allday"] = seeder.create_event(
        a_id,
        name="Allday Fest",
        allday=True,
        start=create_berlin_date(2040, 5, 5),
        end=create_berlin_date(2040, 5, 6),
        place_id=online_id,
    )
    ids["draft"] = seeder.create_event(
        a_id, name="Draft Event", draft=True, start=create_berlin_date(2040, 6, 1, 10)
    )
    ids["planned"] = seeder.create_event(
        a_id,
        name="Planned Event",
        planned=True,
        start=create_berlin_date(2040, 6, 2, 10),
    )
    ids["cancelled"] = seeder.create_event(
        a_id,
        name="Cancelled Event",
        start=create_berlin_date(2040, 7, 1, 10),
        internal_tags="secret",
    )
    ids["past"] = seeder.create_event(
        a_id, name="Past Event", start=create_berlin_date(2020, 1, 2, 14, 30)
    )
    ids["other"] = seeder.create_event(
        b_id, name="Other Event", start=create_berlin_date(2040, 3, 1, 12)
    )
    ids["unverified"] = seeder.create_event(
        c_id, name="Unverified Event", start=create_berlin_date(2040, 3, 1, 13)
    )
    ids["reference"] = seeder.create_reference(ids["other"], a_id)

    with app.app_context():
        full = db.session.get(Event, ids["full"])
        full.photo_id = image_id
        full.tags = "music,live"
        full.internal_tags = "secret,inhouse"
        full.kid_friendly = True
        full.accessible_for_free = True
        full.age_from = 6
        full.age_to = 12
        full.price_info = "Free"
        full.expected_participants = 50
        full.registration_required = True
        full.booked_up = True
        full.ticket_link = "https://example.com/tickets"
        full.rating = 80
        full.categories.append(
            EventCategory.query.order_by(EventCategory.id).offset(19).first()
        )
        db.session.get(Event, ids["cancelled"]).status = EventStatus.cancelled
        db.session.get(EventReference, ids["reference"]).rating = 90
        db.session.get(EventOrganizer, organizer_one).url = "https://example.com/org"
        db.session.get(EventPlace, online_id).url = "https://example.com/online"
        assert CustomEventCategory.query.get(custom_category_id)
        db.session.commit()
        db.session.execute(
            text("UPDATE image SET copyright_text = 'EventCally', license_id = 2")
        )
        db.session.commit()
        _normalize_timestamps(db)

    return ids
