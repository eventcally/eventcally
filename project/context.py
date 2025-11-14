from authlib.integrations.flask_oauth2 import current_token
from flask_security import current_user


class ContextProvider:
    @property
    def current_user(self):  # pragma: no cover
        return current_user

    @property
    def current_user_id_or_none(self):
        if current_user and current_user.is_authenticated:
            return current_user.id

        return None  # pragma: no cover

    @property
    def current_app_installation_id_or_none(self):  # pragma: no cover
        if current_token:
            return current_token.app_installation_id

        return None
