"""Byte-level parity of the organization read endpoints (snapshot captured on the
ORM path, see `tests/integration/presentation/api/read_parity.py`)."""

from datetime import datetime

from sqlalchemy import text

from tests.integration.presentation.api.read_parity import (
    assert_matches_snapshot,
    set_trackable,
)


def test_organization_read_payloads_match_snapshot(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    ids = {
        "alpha": seeder.create_admin_unit(other_user_id, "Alpha Crew", verified=True),
        "crew": seeder.create_admin_unit(other_user_id, "Crew am See", verified=True),
        "zentral": seeder.create_admin_unit(
            other_user_id, "Zentrale", verified=True, short_name="crewzentrale"
        ),
        "unverified": seeder.create_admin_unit(other_user_id, "Unverified Crew"),
    }
    image_id = seeder.upsert_default_image()

    with app.app_context():
        from project.infrastructure.models import AdminUnit, Location

        alpha = db.session.get(AdminUnit, ids["alpha"])
        alpha.url = "https://alpha.example.com"
        alpha.email = "alpha@example.com"
        alpha.phone = "0123"
        alpha.fax = "0124"
        alpha.description = "Beschreibung"
        alpha.logo_id = image_id
        alpha.location = Location(
            street="Markt 1",
            postalCode="38640",
            city="Goslar",
            latitude="51.9077888",
            longitude="10.4333312",
        )
        zentral = db.session.get(AdminUnit, ids["zentral"])
        zentral.location = Location(postalCode="38690", city="Vienenburg")
        db.session.commit()

        for key, (created_at, updated_at) in {
            "alpha": (datetime(2026, 1, 1, 10), datetime(2026, 3, 1, 12)),
            "crew": (datetime(2026, 2, 1, 9), None),
            "zentral": (datetime(2026, 1, 15, 14), datetime(2026, 2, 20, 16)),
            "unverified": (datetime(2026, 1, 20), None),
        }.items():
            set_trackable(db, "adminunit", ids[key], created_at, updated_at)
        set_trackable(db, "adminunit", admin_unit_id, datetime(2025, 12, 1))
        set_trackable(
            db,
            "adminunit",
            seeder.get_eventcally_admin_unit_id(),
            datetime(2025, 11, 1),
        )
        set_trackable(db, "image", image_id, datetime(2026, 1, 2, 8, 30))
        db.session.execute(
            text("UPDATE image SET copyright_text = 'EventCally' WHERE id = :id"),
            {"id": image_id},
        )
        db.session.commit()

    def org_list(**kwargs):
        return utils.get_url("api_v1_organization_list", **kwargs)

    requests = {
        "list": org_list(),
        "list_keyword": org_list(keyword="crew"),
        "list_keyword_sort_created_at": org_list(keyword="crew", sort="-created_at"),
        "list_sort_name": org_list(sort="name"),
        "list_sort_updated_at": org_list(sort="-updated_at"),
        "list_sort_last_modified_at": org_list(sort="-last_modified_at"),
        "list_postal_code": org_list(postal_code="386"),
        "list_postal_codes": org_list(postal_code=["38640", "3869"]),
        "list_created_at_from": org_list(created_at_from="2026-01-12T00:00:00"),
        "list_updated_at_range": org_list(
            updated_at_from="2026-02-01T00:00:00", updated_at_to="2026-02-28T00:00:00"
        ),
        "list_page_2": org_list(page=2, per_page=2),
        "list_out_of_range": org_list(page=5, per_page=2),
        "detail_full": utils.get_url("api_v1_organization", id=ids["alpha"]),
        "detail_own": utils.get_url("api_v1_organization", id=admin_unit_id),
        "detail_unverified": utils.get_url("api_v1_organization", id=ids["unverified"]),
        "detail_unknown": utils.get_url("api_v1_organization", id=4711),
    }

    assert_matches_snapshot("organization", utils, requests)
