class FieldValidationError(Exception):
    """A semantic error of one request field (answered as 422 like a pydantic error).

    Pass `errors` (a list of `(loc, msg)`) to report several fields at once.
    """

    def __init__(
        self,
        loc: list[str] | None = None,
        msg: str | None = None,
        *,
        errors: list[tuple[list[str], str]] | None = None,
    ):
        self.errors = list(errors) if errors else [(loc or [], msg or "")]
        self.loc, self.msg = self.errors[0]
        super().__init__(self.msg)
