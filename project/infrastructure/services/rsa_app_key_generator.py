import hashlib
import secrets

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from project.application.services.abstract_app_key_generator import (
    AbstractAppKeyGenerator,
)


class RsaAppKeyGenerator(AbstractAppKeyGenerator):
    def generate(self) -> tuple[str, str, str, str]:
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        checksum = hashlib.sha256(private_pem).hexdigest()
        kid = secrets.token_urlsafe(16)

        return checksum, kid, public_pem.decode("utf-8"), private_pem.decode("utf-8")
