import datetime

import pytest
from sqlalchemy import text


def _run_cli_command(app, args):
    runner = app.test_cli_runner()
    result = runner.invoke(args=args)

    if result.exit_code != 0:
        print(result.output)
        print(result.exception)

    assert result.exit_code == 0
    return result


def test_update_recurring_dates(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=7")

    runner = app.test_cli_runner()
    result = runner.invoke(args=["event", "update-recurring-dates"])
    assert result.exit_code == 0


def test_update_recurring_dates_adds_missing_dates_and_keeps_existing_ones(
    client, seeder, app, db
):
    from project.models import Event, EventDate

    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=7")
    seeder.create_event(admin_unit_id, None)

    with app.app_context():
        dates = sorted(db.session.get(Event, event_id).dates, key=lambda d: d.start)
        assert len(dates) == 7
        kept = {d.id: d.start for d in dates[:5]}
        for date in dates[5:]:
            db.session.delete(date)
        db.session.commit()

    _run_cli_command(app, ["event", "update-recurring-dates"])

    with app.app_context():
        dates = (
            db.session.query(EventDate)
            .filter(EventDate.event_id == event_id)
            .order_by(EventDate.start)
            .all()
        )
        assert len(dates) == 7
        # The dates that were still right are untouched (same rows)
        assert {d.id: d.start for d in dates[:5]} == kept


def test_update_recurring_dates_writes_silently(client, seeder, app, db):
    from project.models import Event, EventDate, WebhookEvent

    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=3")

    with app.app_context():
        db.session.query(EventDate).filter(EventDate.event_id == event_id).delete()
        db.session.commit()
        webhook_events = db.session.query(WebhookEvent).count()
        last_modified_at = db.session.get(Event, event_id).last_modified_at

    _run_cli_command(app, ["event", "update-recurring-dates"])

    with app.app_context():
        assert db.session.query(EventDate).count() == 3
        assert db.session.query(WebhookEvent).count() == webhook_events
        assert db.session.get(Event, event_id).last_modified_at == last_modified_at


@pytest.mark.parametrize("allday", [False, True])
def test_update_recurring_dates_reads_utc_values_as_berlin_wall_clock(
    client, seeder, app, db, allday
):
    # Stored UTC values must yield Berlin wall-clock dates, also across the DST change
    # at the end of March.
    from project.dateutils import create_berlin_date
    from project.models import EventDate

    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=2")
    utc = datetime.timezone.utc

    if allday:
        # 2030-03-30 00:00 / 23:59:59 Berlin (CET)
        start = datetime.datetime(2030, 3, 29, 23, 0, tzinfo=utc)
        end = datetime.datetime(2030, 3, 30, 22, 59, 59, tzinfo=utc)
    else:
        # 2030-03-30 19:00 - 21:00 Berlin (CET)
        start = datetime.datetime(2030, 3, 30, 18, 0, tzinfo=utc)
        end = datetime.datetime(2030, 3, 30, 20, 0, tzinfo=utc)

    with app.app_context():
        # Raw SQL: the save hooks would re-sanitize the definition, but the nightly job
        # only reads already stored definitions.
        db.session.execute(
            text(
                'UPDATE eventdatedefinition SET start = :start, "end" = :end, '
                "allday = :allday, recurrence_rule = :rule WHERE event_id = :id"
            ),
            {
                "start": start,
                "end": end,
                "allday": allday,
                "rule": "RRULE:FREQ=DAILY;COUNT=2",
                "id": event_id,
            },
        )
        db.session.commit()

    _run_cli_command(app, ["event", "update-recurring-dates"])

    with app.app_context():
        dates = (
            db.session.query(EventDate)
            .filter(EventDate.event_id == event_id)
            .order_by(EventDate.start)
            .all()
        )
        if allday:
            expected = [
                (
                    create_berlin_date(2030, 3, 30),
                    create_berlin_date(2030, 3, 30, 23, 59, 59),
                ),
                (
                    create_berlin_date(2030, 3, 31),
                    create_berlin_date(2030, 3, 31, 23, 59, 59),
                ),
            ]
        else:
            expected = [
                (
                    create_berlin_date(2030, 3, 30, 19),
                    create_berlin_date(2030, 3, 30, 21),
                ),
                (
                    create_berlin_date(2030, 3, 31, 19),
                    create_berlin_date(2030, 3, 31, 21),
                ),
            ]
        assert [(d.start, d.end) for d in dates] == expected
        assert all(d.allday == allday for d in dates)


def test_update_recurring_dates_continues_after_a_broken_event(
    client, seeder, app, db, mocker
):
    from project.models import Event, EventDate

    user_id, admin_unit_id = seeder.setup_base()
    broken_id = seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=3")
    healthy_id = seeder.create_event(admin_unit_id, "RRULE:FREQ=DAILY;COUNT=3")

    with app.app_context():
        db.session.query(EventDate).delete()
        db.session.commit()

    from project.domain.models.aggregates.event_aggregate import EventAggregate

    original = EventAggregate.update_event_dates_with_recurrence_rule

    def fail_for_first(self):
        if self.id == broken_id:
            raise RuntimeError("broken")
        return original(self)

    mocker.patch.object(
        EventAggregate, "update_event_dates_with_recurrence_rule", fail_for_first
    )

    _run_cli_command(app, ["event", "update-recurring-dates"])

    with app.app_context():
        assert db.session.query(Event).count() == 2
        counts = {
            event_id: db.session.query(EventDate)
            .filter(EventDate.event_id == event_id)
            .count()
            for event_id in (broken_id, healthy_id)
        }
        assert counts == {broken_id: 0, healthy_id: 3}


def test_create_event(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()

    _run_cli_command(app, ["test", "event-create", str(admin_unit_id)])
