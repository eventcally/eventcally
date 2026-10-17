class KeySortDefinition(object):
    """A sort option of a query-backed list: only feeds the sort field's choices; the
    view handler maps the selected key onto its list query."""

    def __init__(self, key, **kwargs):
        self.key = key
        self.desc = kwargs.get("desc", key.startswith("-"))
        self.label = kwargs.get("label")

    def __unicode__(self):  # pragma: no cover
        return self.key


def sort_key_or_none(sort_enum, value):
    """Map a submitted sort key onto `sort_enum`; unknown keys fall back to the
    default order."""
    try:
        return sort_enum(value)
    except ValueError:
        return None
