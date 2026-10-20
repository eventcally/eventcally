class FieldValidationError(Exception):
    """A semantic error of one request field (answered as 422 like a pydantic error)."""

    def __init__(self, loc: list[str], msg: str):
        super().__init__(msg)
        self.loc = loc
        self.msg = msg
