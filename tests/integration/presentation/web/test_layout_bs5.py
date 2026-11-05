def test_frame_head_defaults_without_page_meta(client, utils):
    response = utils.get_ok("/eventdates")

    utils.assert_response_contains(
        response, 'name="description" content="Mit der offenen Veranstaltungsdatenbank'
    )
    utils.assert_response_contains(response, 'property="og:image"')
    utils.assert_response_contains(response, 'content="summary"')
    utils.assert_response_contains_not(response, 'rel="canonical"')
    utils.assert_response_contains_not(response, "application/ld+json")


def test_frame_head_uses_the_image_of_the_page_meta(client, app, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    seeder.assign_image_to_event(event_id, seeder.upsert_default_image())

    response = utils.get_ok(utils.get_url("main.event", event_id=event_id))

    utils.assert_response_contains(response, 'content="summary_large_image"')
    utils.assert_response_contains(response, 'property="og:image" content="http')
    utils.assert_response_contains(response, "/image/")
