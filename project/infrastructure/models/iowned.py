class IOwned:
    def before_flush(self, is_dirty):  # pragma: no cover
        raise NotImplementedError
