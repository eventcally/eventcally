def test_organizations(client, seeder, utils):
    url = utils.get_url("organizations")
    utils.get_ok(url)


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("organization_ical", id=admin_unit_id)
    utils.get_ok(url)
