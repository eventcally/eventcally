from project.application.services.abstract_api_key_generator import (
    AbstractApiKeyGenerator,
)
from project.utils import generate_api_key, hash_api_key


class WerkzeugApiKeyGenerator(AbstractApiKeyGenerator):
    def generate(self) -> tuple[str, str]:
        key = generate_api_key()
        return key, hash_api_key(key)
