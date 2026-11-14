import json

from project.infrastructure.logging_config import REACH_LOGGER
from project.presentation.web import reach_log
from tests.integration.log_capture import collect_lines


def source(app, query="", **headers):
    with app.test_request_context(f"/event/1{query}", headers=headers):
        return reach_log.request_source()


def test_src(app):
    assert source(app, "?src=Flyer-2026") == ("flyer-2026", None, None)
    assert source(
        app,
        "?src=a&utm_source=b",
        Referer="https://www.google.com/",
    ) == ("a", None, None)


def test_utm(app):
    assert source(
        app, "?utm_source=newsletter&utm_medium=email&utm_campaign=2026-11"
    ) == (
        "newsletter",
        "email",
        "2026-11",
    )


def test_invalid(app):
    assert source(app, "?src=a b")[0] == "invalid"
    assert source(app, "?src=<x>")[0] == "invalid"
    assert source(app, "?src=a&utm_medium=a b") == ("a", "invalid", None)


def test_referer(app):
    assert (
        source(app, Referer="https://www.Google.com/search?q=x")[0] == "www.google.com"
    )
    assert source(app)[0] == "direct"
    assert source(app, Referer="/relative")[0] == "direct"
    assert source(app, Referer="http://[::1")[0] in ("invalid", "direct")


def test_referer_own_host(app):
    base = "http://localhost"
    assert source(app, Referer=f"{base}/eventdates")[0] == "internal"
    assert source(app, Referer=f"{base}/custom_widget/search?x=1")[0] == "widget"
    assert (
        source(app, Referer=f"{base}/organizations/3/widget/eventdates")[0] == "widget"
    )


def test_is_bot():
    assert reach_log.is_bot("Mozilla/5.0 (compatible; Googlebot/2.1)")
    assert not reach_log.is_bot(
        "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Firefox/120.0"
    )
    assert not reach_log.is_bot(None)


def test_log_event_view(app):
    with collect_lines(REACH_LOGGER) as lines:
        with app.test_request_context("/event/1?src=x"):
            reach_log.log_event_view(1, 2)
    record = json.loads(lines[0])
    assert record["type"] == "reach"
    assert record["event_id"] == 1
    assert record["event_date_id"] == 2
    assert record["source"] == "x"


def test_disabled(app):
    app.config["REACH_LOG"] = False
    with collect_lines(REACH_LOGGER) as lines:
        with app.test_request_context("/event/1"):
            reach_log.log_event_view(1)
    assert lines == []


def test_never_breaks(app, mocker):
    mocker.patch.object(reach_log, "build_event_view_record", side_effect=ValueError)
    log = mocker.patch.object(reach_log.logger, "exception")
    with app.test_request_context("/event/1"):
        reach_log.log_event_view(1)
    log.assert_called_once()
