"""The search of the iframe widget page `/organizations/<id>/widget/eventdates`."""

from types import SimpleNamespace

from project.presentation.shared.legacy_widget_search import legacy_widget_criteria
from project.shared.dateutils import create_berlin_date, get_today


class _QueryBus:
    def handle(self, query):
        return [SimpleNamespace(id=1), SimpleNamespace(id=2)]


def _filters(**kwargs):
    values = dict(
        date_from=None, date_to=None, keyword=None, category_id=None, tag=None
    )
    values.update(kwargs)
    return SimpleNamespace(**values)


def _criteria(**kwargs):
    return legacy_widget_criteria(_QueryBus(), 7, _filters(**kwargs))


def test_defaults_search_from_today_without_planned_events():
    criteria = _criteria()

    assert criteria.date_from == get_today()
    assert criteria.date_to is None
    assert criteria.keyword is None
    assert criteria.category_ids == []
    assert criteria.tags == []
    assert criteria.admin_unit_id == 7
    assert criteria.include_admin_unit_references is True
    assert criteria.include_planned is False


def test_filters_are_applied():
    criteria = _criteria(
        date_from="2030-01-02 10:00:00",
        date_to="2030-01-05T08:00",
        keyword="Konzert",
        category_id="2",
        tag="kultur",
    )

    assert criteria.date_from == create_berlin_date(2030, 1, 2)
    assert criteria.date_to == create_berlin_date(2030, 1, 5, 23, 59, 59)
    assert criteria.keyword == "Konzert"
    assert criteria.category_ids == [2]
    assert criteria.tags == ["kultur"]


def test_an_empty_date_from_means_no_bound():
    criteria = _criteria(date_from="", category_id="0")

    assert criteria.date_from is None
    assert criteria.category_ids == []


def test_one_invalid_filter_resets_all_filters():
    for invalid in (
        dict(date_from="garbage"),
        dict(date_to="2030-13-01"),
        dict(category_id="abc"),
        dict(category_id="99"),
    ):
        criteria = _criteria(keyword="Konzert", tag="kultur", **invalid)

        assert criteria.date_from == get_today()
        assert criteria.date_to is None
        assert criteria.keyword is None
        assert criteria.tags == []
        assert criteria.category_ids == []
