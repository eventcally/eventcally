from flask_babel import lazy_gettext


class BaseFilter(object):
    def __init__(self, column, **kwargs):
        self.column = column
        self.key = kwargs.get("key", column.key)
        self.label = kwargs.get("label")
        self.options = kwargs.get("options")

    def apply(self, query, value):  # pragma: no cover
        raise NotImplementedError()

    def get_column(self, alias):
        return self.column if alias is None else getattr(alias, self.column.key)

    def __unicode__(self):  # pragma: no cover
        return self.key


class BooleanFilter(BaseFilter):
    def __init__(self, column, **kwargs):
        kwargs.setdefault(
            "options",
            (
                ("", lazy_gettext("All")),
                ("1", lazy_gettext("Yes")),
                ("0", lazy_gettext("No")),
            ),
        )
        super().__init__(
            column,
            **kwargs,
        )

    def apply(self, query, value, alias=None):
        if value == "1":
            return query.filter(self.get_column(alias).is_(True))

        if value == "0":
            return query.filter(self.get_column(alias).is_(False))

        return query  # pragma: no cover
