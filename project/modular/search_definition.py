class KeySearchDefinition(object):
    """Enables the keyword field of a query-backed list; the view handler maps the
    keyword onto its list query."""

    def __init__(self, key, **kwargs):
        self.key = key
        self.desc = kwargs.get("desc")
        self.label = kwargs.get("label")

    def __unicode__(self):  # pragma: no cover
        return self.key
