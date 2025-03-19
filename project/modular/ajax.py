from flask import request

from project import db
from project.models.event_category import EventCategory
from project.modular.search_definition import apply_search_definitions
from project.utils import get_event_category_name
from project.views.event import get_event_category_choices


def get_primary_key(model):
    """
    Return primary key name from a model. If the primary key consists of multiple columns,
    return the corresponding tuple

    :param model:
        Model class
    """
    mapper = model._sa_class_manager.mapper
    pks = [mapper.get_property_by_column(c).key for c in mapper.primary_key]
    if len(pks) == 1:
        return pks[0]

    if len(pks) > 1:  # pragma: no cover
        return tuple(pks)

    return None  # pragma: no cover


class AjaxModelLoader:
    def __init__(self, session, model, **kwargs):
        self.session = session
        self.model = model
        self.pk = get_primary_key(model)
        self.placeholder = kwargs.pop("placeholder", None)
        self.search_definitions = kwargs.pop("search_definitions", None)
        self.sort_definitions = kwargs.pop("sort_definitions", None)
        self.minimum_input_length = int(kwargs.pop("minimum_input_length", 0))
        self.options = kwargs

    def format(self, model):
        if not model:  # pragma: no cover
            return None

        return getattr(model, self.pk), self.format_model(model)

    def format_model(self, model):
        return str(model)

    def get_query(self):
        return self.session.query(self.model)

    def get_one(self, pk):
        # prevent autoflush from occuring during populate_obj
        with self.session.no_autoflush:
            return self.get_query().filter_by(id=pk).first()

    def get_pagination(self, term):
        query = self.get_query()
        query = self.apply_query_filter(query, term)
        query = self.apply_query_order(query)
        return query.paginate()

    def apply_query_filter(self, query, term):
        query = apply_search_definitions(query, self.search_definitions, term)
        return query

    def apply_query_order(self, query):
        if self.sort_definitions:
            for definition in self.sort_definitions:
                query = definition.apply(query)

        return query

    def get_ajax_pagination(self, term):
        pagination = self.get_pagination(term)
        result = {
            "items": [self.format(m) for m in pagination.items],
            "has_next": pagination.has_next,
        }
        return result


class EventCategoryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, **kwargs):
        super().__init__(db.session, EventCategory, **kwargs)

    def get_ajax_pagination(self, term):
        all = get_event_category_choices()
        matching = [i for i in all if term in i[1]] if term else all

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        start = (page - 1) * per_page
        end = start + per_page
        sliced = matching[start:end]

        result = {
            "items": sliced,
            "has_next": len(matching) > len(sliced),
        }
        return result

    def format_model(self, model):
        return get_event_category_name(model)
