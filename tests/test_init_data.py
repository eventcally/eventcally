import pytest


@pytest.mark.parametrize("insecure", [None, "0", "1"])
def test_add_oauth2_scheme(app, utils, insecure):
    import os

    if insecure:
        os.environ["AUTHLIB_INSECURE_TRANSPORT"] = insecure
    else:
        del os.environ["AUTHLIB_INSECURE_TRANSPORT"]

    url = utils.get_url("home")
    utils.get_ok(url)
