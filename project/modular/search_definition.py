from sqlalchemy import or_

from project.utils import parse_like_term


class BaseSearchDefinition(object):
    def __init__(self, column, **kwargs):
        self.column = column
        self.desc = kwargs.get("desc")
        self.label = kwargs.get("label")
        self.key = kwargs.get("key", column.key)

    def get_filter(self, value):  # pragma: no cover
        raise NotImplementedError()

    def get_column(self, alias=None):
        return self.column if alias is None else getattr(alias, self.column.key)

    def __unicode__(self):  # pragma: no cover
        return self.key


class SearchDefinition(BaseSearchDefinition):
    def get_filter(self, value):
        like = parse_like_term(value)
        return self.get_column().ilike(like)


def apply_search_definitions(query, search_definitions, keyword):
    if not search_definitions or not keyword:  # pragma: no cover
        return query

    filter_stmt = []

    for definition in search_definitions:
        filter = definition.get_filter(keyword)
        filter_stmt.append(filter)

    query = query.filter(or_(*filter_stmt))
    return query
