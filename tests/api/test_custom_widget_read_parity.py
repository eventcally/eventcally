"""Byte-level parity of the custom widget read endpoints (snapshot captured on the
ORM path, see `tests/api/read_parity.py`)."""

from datetime import datetime

from tests.api.read_parity import assert_matches_snapshot, set_trackable


def test_custom_widget_read_payloads_match_snapshot(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Andere Crew"
    )
    ids = [
        seeder.insert_event_custom_widget(admin_unit_id, name="Zeta Suche"),
        seeder.insert_event_custom_widget(admin_unit_id, name="alpha Widget"),
        seeder.insert_event_custom_widget(admin_unit_id, name="Mitte Suche"),
    ]
    foreign_id = seeder.insert_event_custom_widget(other_admin_unit_id, name="Fremd")

    with app.app_context():
        for object_id, stamp in zip(ids, [1, 2, 3]):
            set_trackable(db, "customwidget", object_id, datetime(2026, 1, stamp), None)
        set_trackable(db, "customwidget", foreign_id, datetime(2026, 1, 4), None)
        db.session.commit()

    def widget_list(**kwargs):
        return utils.get_url(
            "api_v1_organization_custom_widget_list", id=admin_unit_id, **kwargs
        )

    requests = {
        "list": widget_list(),
        "list_name": widget_list(name="such"),
        "list_page_2": widget_list(page=2, per_page=2),
        "list_out_of_range": widget_list(page=3, per_page=2),
        "detail": utils.get_url("api_v1_custom_widget", id=ids[0]),
        "detail_foreign": utils.get_url("api_v1_custom_widget", id=foreign_id),
        "detail_unknown": utils.get_url("api_v1_custom_widget", id=4711),
        "js_loader": utils.get_url("main.js_widget_loader_custom_widget", id=ids[1]),
        "js_loader_unknown": utils.get_url(
            "main.js_widget_loader_custom_widget", id=4711
        ),
    }

    assert_matches_snapshot("custom_widget", utils, requests)
