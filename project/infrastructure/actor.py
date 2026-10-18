from authlib.integrations.flask_oauth2 import current_token
from flask_security import current_user


class Actor:
    @staticmethod
    def current_user_id_or_none():
        if current_user and current_user.is_authenticated:
            return current_user.id

        return None

    @staticmethod
    def current_app_installation_id_or_none():
        if current_token:
            return current_token.app_installation_id

        return None


current_actor: Actor = Actor()
