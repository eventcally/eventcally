import re

import pytest


def test_generated_request_id(client, utils):
    response = utils.get_ok(utils.get_url("main.home"))

    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])


def test_incoming_request_id_is_echoed(client, utils):
    response = client.get(
        utils.get_url("main.home"), headers={"X-Request-ID": "a.B_1-2"}
    )

    assert response.headers["X-Request-ID"] == "a.B_1-2"


@pytest.mark.parametrize("incoming", ["a b", "x" * 129, "<script>"])
def test_malformed_request_id_is_replaced(client, utils, incoming):
    response = client.get(
        utils.get_url("main.home"), headers={"X-Request-ID": incoming}
    )

    assert re.fullmatch(r"[0-9a-f]{32}", response.headers["X-Request-ID"])


def test_log_lines_of_the_request_carry_its_id():
    from project.factory import create_app
    from project.infrastructure.logging_config import get_log_context

    test_app = create_app({"TESTING": True})
    test_app.add_url_rule("/log-context", "log_context", lambda: get_log_context())

    response = test_app.test_client().get(
        "/log-context", headers={"X-Request-ID": "r-1"}
    )

    assert response.json == {"request_id": "r-1"}
    assert get_log_context() == {}
