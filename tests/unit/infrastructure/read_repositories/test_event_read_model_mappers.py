"""Mapper edge cases that need no database."""

from project.infrastructure.read_repositories import event_read_model_mappers as m


def test_missing_embedded_objects_stay_missing():
    assert m._to_organizer(None) is None
    assert m._to_place(None) is None


def test_batch_lookups_without_ids_do_not_query():
    class NoSession:
        def execute(self, *args, **kwargs):  # pragma: no cover
            raise AssertionError("no query expected")

    session = NoSession()

    assert m.verified_admin_units(session, []) == {}
    assert m.reference_ids(session, [], 1) == {}
    assert m.reference_ids(session, [1], None) == {}
    assert m.event_references(session, []) == {}
    assert m.event_reference_requests(session, []) == {}
    assert m.event_counts(session, []) == {}
