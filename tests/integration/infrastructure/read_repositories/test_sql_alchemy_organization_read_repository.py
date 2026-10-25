"""SqlAlchemyOrganizationReadRepository against the database."""

import pytest

from project.application.queries import (
    ListVerifierOrganizationsQuery,
    SearchOrganizationsQuery,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.organization_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def _search_ids(read_repo, **kwargs):
    page = read_repo(
        "search", SearchOrganizationsQuery(include_unverified=True, **kwargs)
    )
    return [item.id for item in page.items]


def test_search_filters(app, db, read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    verifier_id = seeder.create_admin_unit(
        seeder.create_user("v@test.de"),
        "Verifier Crew",
        can_verify_other=True,
        incoming_verification_requests_allowed=True,
    )
    plain_id = seeder.create_admin_unit(seeder.create_user("p@test.de"), "Plain Crew")

    only_verifier = _search_ids(read_repo, only_verifier=True)
    assert verifier_id in only_verifier
    assert plain_id not in only_verifier

    reference_targets = _search_ids(
        read_repo, reference_request_for_admin_unit_id=plain_id
    )
    assert verifier_id in reference_targets
    assert admin_unit_id in reference_targets
    assert plain_id not in reference_targets

    in_location = _search_ids(read_repo, postal_codes=["123"])
    assert {admin_unit_id, plain_id, verifier_id} <= set(in_location)
    assert _search_ids(read_repo, postal_codes=["999"]) == []

    crews = _search_ids(read_repo, keyword="crew")
    assert {admin_unit_id, plain_id, verifier_id} <= set(crews)
    assert _search_ids(read_repo, keyword="plain") == [plain_id]
    assert _search_ids(read_repo, keyword="verifiercrew") == [verifier_id]
    verified_only = read_repo("search", SearchOrganizationsQuery())
    assert plain_id not in [item.id for item in verified_only.items]


def test_search_by_incoming_verification_postal_code(app, db, read_repo, seeder):
    seeder.setup_base(log_in=False)
    open_id = seeder.create_admin_unit(
        seeder.create_user("o@test.de"),
        "Open Crew",
        incoming_verification_requests_postal_codes=[],
    )
    matching_id = seeder.create_admin_unit(
        seeder.create_user("m@test.de"),
        "Matching Crew",
        incoming_verification_requests_postal_codes=["12345"],
    )
    seeder.create_admin_unit(
        seeder.create_user("x@test.de"),
        "Other Crew",
        incoming_verification_requests_postal_codes=["99999"],
    )

    ids = _search_ids(read_repo, incoming_verification_requests_postal_code="12345")

    assert matching_id in ids
    assert open_id in ids
    assert len(ids) == len([i for i in ids if i != 0])


def test_list_verifiers(app, db, read_repo, seeder):
    seeder.setup_base(log_in=False)
    verifier_id = seeder.create_admin_unit(
        seeder.create_user("v@test.de"),
        "Verifier Crew",
        can_verify_other=True,
        incoming_verification_requests_allowed=True,
        incoming_verification_requests_text="Send us a mail",
        verified=True,
    )

    page = read_repo(
        "list_verifiers", ListVerifierOrganizationsQuery(postal_code="12345")
    )

    assert page.total == 1
    assert page.items[0].id == verifier_id
    assert page.items[0].is_verified is True
    assert page.items[0].incoming_verification_requests_text == "Send us a mail"


def test_get(app, db, read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    organization = read_repo("get", admin_unit_id)

    assert organization.id == admin_unit_id
    assert organization.name == "Meine Crew"
    assert organization.short_name == "meinecrew"
    assert organization.location.city == "City"
    assert organization.incoming_reference_requests_allowed is True
    assert organization.can_verify_other is False
    assert read_repo("get", 4711) is None
