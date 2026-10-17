from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class OAuth2ClientReadModel(BaseReadModel):
    """An OAuth2 client (or app) as its list, read, update and delete pages show it.
    `grant_types`, `response_types` and `token_endpoint_auth_method` are the fixed
    values of the ORM model."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: Optional[ObjectId] = None
    user_id: Optional[ObjectId] = None
    client_id: str
    client_secret: Optional[str] = None
    client_name: Optional[str] = None
    client_uri: Optional[str] = None
    scope: str = ""
    redirect_uris: List[str] = []
    grant_types: List[str] = [
        "authorization_code",
        "refresh_token",
        "client_credentials",
        "urn:ietf:params:oauth:grant-type:jwt-bearer",
    ]
    response_types: List[str] = ["code"]
    token_endpoint_auth_method: List[str] = [
        "client_secret_basic",
        "client_secret_post",
        "none",
    ]
    audit: Optional[AuditReadModel] = None  # get queries only


class WebhookReadModel(BaseReadModel):
    """Fills `WebhookForm` (attribute names equal its fields)."""

    model_config = ConfigDict(frozen=True)

    url: Optional[str] = None
    secret: Optional[str] = None
    disabled: bool = False
    event_types: List[str] = []


class AppReadModel(OAuth2ClientReadModel):
    app_permissions: List[str] = []
    homepage_url: Optional[str] = None
    setup_url: Optional[str] = None
    description: Optional[str] = None
    webhook: Optional[WebhookReadModel] = None
