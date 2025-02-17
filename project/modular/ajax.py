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
    def __init__(self, session, model, **options):
        self.options = options
        self.session = session
        self.model = model
        self.pk = get_primary_key(model)

    def format(self, model):
        if not model:  # pragma: no cover
            return None

        return getattr(model, self.pk), str(model)

    def get_query(self):
        return self.session.query(self.model)

    def get_one(self, pk):
        # prevent autoflush from occuring during populate_obj
        with self.session.no_autoflush:
            return self.get_query().get(pk)

    def get_pagination(self, term):  # pragma: no cover
        query = self.get_query()
        return query.paginate()

    def get_ajax_pagination(self, term):
        pagination = self.get_pagination(term)
        result = {
            "items": [self.format(m) for m in pagination.items],
            "has_next": pagination.has_next,
        }
        return result
