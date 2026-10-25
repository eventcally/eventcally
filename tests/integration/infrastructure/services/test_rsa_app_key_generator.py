import hashlib

from cryptography.hazmat.primitives import serialization

from project.infrastructure.services.rsa_app_key_generator import RsaAppKeyGenerator


def test_generate_returns_matching_checksum_kid_and_key_pair():
    checksum, kid, public_pem, private_pem = RsaAppKeyGenerator().generate()

    assert checksum == hashlib.sha256(private_pem.encode("utf-8")).hexdigest()
    assert kid
    private_key = serialization.load_pem_private_key(
        private_pem.encode("utf-8"), password=None
    )
    public_key = serialization.load_pem_public_key(public_pem.encode("utf-8"))
    assert private_key.public_key().public_numbers() == public_key.public_numbers()
    assert private_key.key_size == 2048


def test_generate_is_random():
    generator = RsaAppKeyGenerator()

    assert generator.generate()[1] != generator.generate()[1]
