class _Unset:
    def __bool__(self):
        return False

    def __copy__(self):  # pragma: no cover
        return self

    def __deepcopy__(self, _):
        return self

    def __repr__(self):  # pragma: no cover
        return "<project.unset>"


unset = _Unset()
