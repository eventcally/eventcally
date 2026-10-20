from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from project.application.read_models.page import Page
from project.application.read_models.user_admin_read_models import UserAdminReadModel


class AdminUserRow(BaseModel):
    id: int
    email: str
    created_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    tos_accepted_at: Optional[datetime] = None
    deletion_requested_at: Optional[datetime] = None
    roles: List[str] = []


class AdminRoleOption(BaseModel):
    name: str
    title: str


class AdminUserDetail(BaseModel):
    user: AdminUserRow
    available_roles: List[AdminRoleOption]


class AdminUserRolesUpdate(BaseModel):
    roles: List[str]


class AdminUserDelete(BaseModel):
    email: str = Field(min_length=1)


class AdminUserPage(BaseModel):
    items: List[AdminUserRow]
    page: int
    per_page: int
    total: int
    pages: int

    @classmethod
    def from_page(cls, page: Page[UserAdminReadModel]) -> "AdminUserPage":
        return cls(
            items=[AdminUserRow(**u.model_dump()) for u in page.items],
            page=page.page,
            per_page=page.per_page,
            total=page.total,
            pages=page.pages,
        )


class AdminSettings(BaseModel):
    start_page: Optional[str] = None
    tos: Optional[str] = None
    legal_notice: Optional[str] = None
    contact: Optional[str] = None
    privacy: Optional[str] = None
    announcement: Optional[str] = None


class AdminSettingUpdate(BaseModel):
    value: Optional[str] = Field(...)


class AdminPlanning(BaseModel):
    planning_external_calendars: Optional[str] = None


class AdminPlanningUpdate(BaseModel):
    planning_external_calendars: Optional[str] = Field(...)
