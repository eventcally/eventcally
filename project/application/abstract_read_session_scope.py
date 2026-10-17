import abc


class AbstractReadSessionScope(abc.ABC):
    """One read transaction per top-level query.

    Implementations must be re-entrant: only the outermost exit releases the
    session, so a handler that dispatches a nested query shares the transaction.
    """

    @abc.abstractmethod
    def __enter__(self) -> "AbstractReadSessionScope":  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None:  # pragma: no cover
        raise NotImplementedError
