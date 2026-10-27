import warnings

from swagger_spec_validator import validator20
from swagger_spec_validator.common import SwaggerValidationWarning


def test_swagger(utils):
    response = utils.get_ok("/swagger/")
    # $ref siblings are ignored in Swagger 2.0 (e.g. a lost x-nullable): fail on them
    with warnings.catch_warnings():
        warnings.simplefilter("error", SwaggerValidationWarning)
        validator20.validate_spec(response.json)


def test_swagger_ui(utils):
    utils.get_ok("/swagger-ui/")
