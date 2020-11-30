def test_home(client, seeder, utils):
    url = utils.get_url("home")
    utils.get_ok(url)

    url = utils.get_url("home", src="infoscreen")
    response = client.get(url)
    utils.assert_response_redirect(response, "home")


def test_example(client, seeder, utils):
    url = utils.get_url("example")
    utils.get_ok(url)


def test_impressum(client, seeder, utils):
    url = utils.get_url("impressum")
    utils.get_ok(url)


def test_datenschutz(client, seeder, utils):
    url = utils.get_url("datenschutz")
    utils.get_ok(url)


def test_developer(client, seeder, utils):
    url = utils.get_url("developer")
    utils.get_ok(url)
