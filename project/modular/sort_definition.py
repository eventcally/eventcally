class BaseSortDefinition(object):
    def __init__(self, column, **kwargs):
        self.column = column
        self.desc = kwargs.get("desc")
        self.label = kwargs.get("label")
        self.func = kwargs.get("func")

        prefix = "-" if self.desc else ""
        self.key = kwargs.get("key", f"{prefix}{column.key}")

    def apply(self, query):  # pragma: no cover
        raise NotImplementedError()

    def get_column(self, alias=None):
        return self.column if alias is None else getattr(alias, self.column.key)

    def __unicode__(self):  # pragma: no cover
        return self.key


class SortDefinition(BaseSortDefinition):
    def apply(self, query):
        comp = self.func(self.get_column()) if self.func else self.get_column()

        if self.desc:
            return query.order_by(comp.desc())

        return query.order_by(comp)
