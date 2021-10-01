def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())

    url = utils.get_url("event_date", id=1)
    utils.get_ok(url)

    url = utils.get_url("event_date", id=1, src="home")
    response = client.get(url)
    utils.assert_response_redirect(response, "event_date", id=1)

    seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("event_date", id=2)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    seeder.create_event_unverified()
    url = utils.get_url("event_date", id=3)
    response = utils.get(url)


def test_ical(client, seeder, utils):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    # Default
    event_id = seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("event_date_ical", id=event_id)
    utils.get_ok(url)

    # Draft
    draft_id = seeder.create_event(
        admin_unit_id,
        draft=True,
        start=create_berlin_date(2020, 1, 2, 14, 30),
        end=create_berlin_date(2020, 1, 3, 14, 30),
    )
    url = utils.get_url("event_date_ical", id=draft_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    # Unverified
    _, _, unverified_id = seeder.create_event_unverified()
    url = utils.get_url("event_date_ical", id=unverified_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    # All-day single day
    allday_id = seeder.create_event(
        admin_unit_id, allday=True, start=create_berlin_date(2020, 1, 2, 14, 30)
    )
    url = utils.get_url("event_date_ical", id=allday_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "DTSTART;VALUE=DATE:20200102")
    utils.assert_response_contains_not(response, "DTEND;VALUE=DATE:")

    # All-day multiple days
    allday_id = seeder.create_event(
        admin_unit_id,
        allday=True,
        start=create_berlin_date(2020, 1, 2, 14, 30),
        end=create_berlin_date(2020, 1, 3, 14, 30),
    )
    url = utils.get_url("event_date_ical", id=allday_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "DTSTART;VALUE=DATE:20200102")
    utils.assert_response_contains(response, "DTEND;VALUE=DATE:20200104")


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("event_dates")
    utils.get_ok(url)

    url = utils.get_url("event_dates", keyword="name")
    utils.get_ok(url)

    url = utils.get_url("event_dates", category_id=2000)
    utils.get_ok(url)
