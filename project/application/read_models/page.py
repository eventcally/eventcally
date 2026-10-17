from typing import Generic, List, Optional, TypeVar

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel

T = TypeVar("T")


class Page(BaseReadModel, Generic[T]):
    """One page of query results.

    The properties mirror Flask-SQLAlchemy's `Pagination`, so templates,
    `get_pagination_urls` and the API pagination schema read it unchanged. They are
    plain properties, not computed fields, so they are not serialized.
    """

    model_config = ConfigDict(frozen=True)

    items: List[T]
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        if not self.total or not self.per_page:
            return 0

        return -(-self.total // self.per_page)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def prev_num(self) -> Optional[int]:
        if not self.has_prev:
            return None

        return self.page - 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def next_num(self) -> Optional[int]:
        if not self.has_next:
            return None

        return self.page + 1

    @property
    def is_out_of_range(self) -> bool:
        """True where Flask-SQLAlchemy's `paginate(error_out=True)` would 404."""
        return self.page > 1 and not self.items
