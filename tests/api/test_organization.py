def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("organizationresource", id=admin_unit_id)
    utils.get_ok(url)


def test_list(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("organizationlistresource", keyword="crew")
    utils.get_ok(url)


def test_read_by_short_name(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("organizationbyshortnameresource", short_name="meinecrew")
    utils.get_ok(url)


def test_event_date_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("organizationeventdatesearchresource", id=admin_unit_id)
    utils.get_ok(url)


def test_event_search(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("organizationeventsearchresource", id=admin_unit_id)
    utils.get_ok(url)


def test_organizers(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "organizationorganizerlistresource", id=admin_unit_id, name="crew"
    )
    utils.get_ok(url)


def test_places(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("organizationplacelistresource", id=admin_unit_id, name="crew")
    utils.get_ok(url)
