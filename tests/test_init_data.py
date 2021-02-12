def test_add_oauth2_scheme(app, utils):
    import os

    del os.environ["AUTHLIB_INSECURE_TRANSPORT"]

    url = utils.get_url("home")
    utils.get_ok(url)
