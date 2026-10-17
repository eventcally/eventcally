import datetime
import time
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId

_GMT = ZoneInfo("GMT")


class OAuth2TokenReadModel(BaseReadModel):
    """A user's OAuth2 token as the token list and revoke page show it. Mirrors the
    Authlib `OAuth2TokenMixin` checks the display calls."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    user_id: Optional[ObjectId] = None
    client_name: Optional[str] = None
    scope: Optional[str] = None
    issued_at: int
    expires_in: int = 0
    access_token_revoked_at: int = 0
    refresh_token_revoked_at: int = 0

    @property
    def issued_at_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.issued_at, _GMT)

    @property
    def expires_at_datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.issued_at + self.expires_in, _GMT)

    def is_expired(self) -> bool:
        if not self.expires_in:
            return False

        return self.issued_at + self.expires_in < time.time()

    def is_revoked(self):
        return self.access_token_revoked_at or self.refresh_token_revoked_at
