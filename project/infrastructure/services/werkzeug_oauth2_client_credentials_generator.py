from werkzeug.security import gen_salt

from project.application.services.abstract_oauth2_client_credentials_generator import (
    AbstractOAuth2ClientCredentialsGenerator,
)


class WerkzeugOAuth2ClientCredentialsGenerator(
    AbstractOAuth2ClientCredentialsGenerator
):
    def generate(self) -> tuple[str, str]:
        return gen_salt(24), gen_salt(48)
