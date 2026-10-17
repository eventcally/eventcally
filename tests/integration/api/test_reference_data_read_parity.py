"""Byte-level parity of the reference data list endpoints (snapshot captured on
the ORM path, see `tests/integration/api/read_parity.py`)."""

from tests.integration.api.read_parity import assert_matches_snapshot


def test_reference_data_payloads_match_snapshot(seeder, utils):
    seeder.setup_api_access()
    category_set_id, _ = seeder.get_one_custom_event_category_set()

    requests = {
        "licenses": utils.get_url("api_v1_license_list"),
        "licenses_page_2": utils.get_url("api_v1_license_list", page=2, per_page=2),
        "licenses_out_of_range": utils.get_url(
            "api_v1_license_list", page=50, per_page=2
        ),
        "event_categories": utils.get_url("api_v1_event_category_list", per_page=50),
        "event_categories_page_2": utils.get_url(
            "api_v1_event_category_list", page=2, per_page=5
        ),
        "category_sets": utils.get_url("api_v1_custom_event_category_set_list"),
        "categories_of_set": utils.get_url(
            "api_v1_custom_event_category_set_event_category_list",
            id=category_set_id,
            per_page=50,
        ),
        "categories_of_set_page_2": utils.get_url(
            "api_v1_custom_event_category_set_event_category_list",
            id=category_set_id,
            page=2,
            per_page=3,
        ),
        "categories_of_unknown_set": utils.get_url(
            "api_v1_custom_event_category_set_event_category_list", id=4711
        ),
    }

    assert_matches_snapshot("reference_data", utils, requests)
