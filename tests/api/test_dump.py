def test_read(client, seeder, utils):
    response = utils.get_endpoint("api_v1_dump")
    utils.assert_response_notFound(response)
