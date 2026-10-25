from project.infrastructure.services.werkzeug_api_key_generator import (
    WerkzeugApiKeyGenerator,
)
from project.shared.utils import hash_api_key


def test_generate_returns_key_and_its_hash(app):
    with app.app_context():
        key, key_hash = WerkzeugApiKeyGenerator().generate()
        expected_hash = hash_api_key(key)

    assert key
    assert key_hash == expected_hash
    assert key != key_hash
