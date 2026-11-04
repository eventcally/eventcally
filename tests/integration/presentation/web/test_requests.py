def test_api_responses_skip_the_site_headers(app, utils):
    app.config["API_READ_ANONYM"] = True

    response = utils.get_json_ok(utils.get_url("api_v1_organization_list"))

    assert "X-Frame-Options" not in response.headers
    assert "Content-Security-Policy" not in response.headers


def _user_without_tos(seeder, utils):
    seeder.create_user(tos_accepted=False)
    utils.login()


def test_tos_gate_redirects_other_pages_and_bff_reads(client, seeder, utils):
    _user_without_tos(seeder, utils)

    response = client.get("/profile")
    assert response.status_code == 302
    assert "/user/accept-tos" in response.headers["Location"]

    response = client.get("/bff/user/profile")
    assert response.status_code == 302
    assert "/user/accept-tos" in response.headers["Location"]


def test_tos_gate_lets_the_confirmation_page_and_its_bff_routes_through(
    client, seeder, utils
):
    _user_without_tos(seeder, utils)

    utils.get_ok("/user/accept-tos?next=/manage")

    assert utils.get_json("/bff/user/accept-tos").status_code == 200
    response = utils.post_json(
        "/bff/user/accept-tos?next=/manage", {"accept_tos": True}
    )
    assert response.status_code == 200
    assert response.json == {"redirect_url": "/manage"}

    # Accepted: the gate lets the pages through now.
    utils.get_ok("/profile")
