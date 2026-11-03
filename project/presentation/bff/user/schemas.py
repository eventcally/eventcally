from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from project.application.read_models.page import Page
from project.presentation.bff.schemas import PageParams


class UserRedirect(BaseModel):
    redirect_url: str


class UserAudit(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None


class _UserPage(BaseModel):
    page: int
    per_page: int
    total: int
    pages: int

    @staticmethod
    def paging(page: Page) -> dict:
        return dict(
            page=page.page,
            per_page=page.per_page,
            total=page.total,
            pages=page.pages,
        )


# Profile, settings, deletion, terms of service


class UserProfile(BaseModel):
    email: str
    locale: Optional[str] = None
    newsletter_enabled: bool
    deletion_requested_at: Optional[datetime] = None


class UserGeneralSettingsSave(BaseModel):
    locale: Optional[Literal["de", "en"]] = None


class UserNotificationSettingsSave(BaseModel):
    newsletter_enabled: bool


class UserDeletionConfirm(BaseModel):
    email: str = Field(min_length=1)


class UserAcceptTosForm(BaseModel):
    has_tos: bool


class UserAcceptTosParams(BaseModel):
    # Read by Flask-Security's `get_post_login_redirect` from the query string; declared
    # for the contract only.
    next: Optional[str] = None


class UserAcceptTosSave(BaseModel):
    accept_tos: Literal[True]


# API keys


class UserApiKeyListParams(PageParams):
    # The values of `ApiKeySort` (a plain literal keeps the OpenAPI parameter inline).
    sort: Optional[Literal["name", "-created_at"]] = None


class UserApiKeyListItem(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None


class UserApiKeyPage(_UserPage):
    items: List[UserApiKeyListItem]


class UserApiKeySave(BaseModel):
    name: str = Field(min_length=1)


class UserApiKeyCreated(BaseModel):
    id: int
    key: str


class UserApiKeyDetail(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    rate_limits: List[str]
    audit: Optional[UserAudit] = None


class UserNameConfirm(BaseModel):
    name: str = Field(min_length=1)


# OAuth2 clients and tokens


class UserOAuth2ClientListItem(BaseModel):
    id: int
    client_name: Optional[str] = None


class UserOAuth2ClientPage(_UserPage):
    items: List[UserOAuth2ClientListItem]


class UserOAuth2ClientForm(BaseModel):
    scopes: List[str]


class UserOAuth2ClientSave(BaseModel):
    client_name: str = Field(min_length=1)
    redirect_uris: List[str] = []
    scopes: List[str] = []


class UserOAuth2ClientCreated(BaseModel):
    id: int


class UserOAuth2ClientDetail(BaseModel):
    id: int
    client_id: str
    client_secret: Optional[str] = None
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    scope: str
    scopes: List[str]
    redirect_uris: List[str]
    grant_types: List[str]
    response_types: List[str]
    token_endpoint_auth_method: List[str]
    audit: Optional[UserAudit] = None


class UserOAuth2Token(BaseModel):
    id: int
    client_name: Optional[str] = None
    scope: Optional[str] = None
    issued_at: datetime
    expires_at: datetime
    status: Optional[Literal["expired", "revoked"]] = None


class UserOAuth2TokenPage(_UserPage):
    items: List[UserOAuth2Token]


# Memberships and invitations


class UserMembershipItem(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    is_admin: bool


class UserMembershipPage(_UserPage):
    items: List[UserMembershipItem]


class UserMembershipDetail(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    can_leave: bool


class UserMemberInvitationItem(BaseModel):
    id: int
    organization_id: int
    organization_name: str


class UserMemberInvitationPage(_UserPage):
    items: List[UserMemberInvitationItem]


class UserOrganizationInvitationItem(BaseModel):
    id: int
    organization_id: int
    organization_name: str
    name: Optional[str] = None
    created_at: Optional[datetime] = None


class UserOrganizationInvitationPage(_UserPage):
    items: List[UserOrganizationInvitationItem]
