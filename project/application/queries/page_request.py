from pydantic import Field

from project.domain.types.custom_base_model import CustomBaseModel

DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100


class PageRequest(CustomBaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page
