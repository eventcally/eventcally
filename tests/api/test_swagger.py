from swagger_spec_validator import validator20


def test_swagger(utils):
    response = utils.get_ok("/swagger/")
    validator20.validate_spec(response.json)


def test_swagger_ui(utils):
    utils.get_ok("/swagger-ui/")
