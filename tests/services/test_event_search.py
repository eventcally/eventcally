def test_date_str(client, seeder, utils):
    from project.dateutils import create_berlin_date
    from project.services.search_params import EventSearchParams

    params = EventSearchParams()
    params.date_from = create_berlin_date(2030, 12, 30, 0)
    params.date_to = create_berlin_date(2030, 12, 31, 0)

    assert params.date_from_str == "2030-12-30"
    assert params.date_to_str == "2030-12-31"
