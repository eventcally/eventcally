from project import db
from project.models.app_installation_generated import AppInstallationGeneratedMixin
from project.models.app_key_generated import AppKeyGeneratedMixin


class AppInstallation(db.Model, AppInstallationGeneratedMixin):
    pass


class AppKey(db.Model, AppKeyGeneratedMixin):
    def generate_key(self) -> bytes:
        import hashlib
        import secrets

        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # RSA Private Key erzeugen
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        # Private Key exportieren
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Public Key exportieren
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        self.checksum = hashlib.sha256(private_pem).hexdigest()
        self.kid = secrets.token_urlsafe(16)
        self.public_key = public_pem.decode("utf-8")

        return private_pem

    def get_jwk(self):
        from authlib.jose import JsonWebKey

        return JsonWebKey.import_key(
            self.public_key, options={"kty": "RSA", "kid": self.kid}
        )
