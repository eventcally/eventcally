from typing import List

from pydantic import BaseModel, Field

from project.application.queries.page_request import (
    DEFAULT_PER_PAGE,
    MAX_PER_PAGE,
    PageRequest,
)


class ErrorResponse(BaseModel):
    name: str
    message: str


class FieldError(BaseModel):
    loc: List[str]
    msg: str


class ValidationErrorResponse(ErrorResponse):
    errors: List[FieldError]


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE)

    def to_page_request(self) -> PageRequest:
        return PageRequest(page=self.page, per_page=self.per_page)
