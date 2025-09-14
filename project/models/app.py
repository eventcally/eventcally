from flask_security import AsaList
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.mutable import MutableList

from project import db
from project.models.trackable_mixin import TrackableMixin


class AppInstallation(db.Model, TrackableMixin):
    __tablename__ = "app_installation"
    __table_args__ = (UniqueConstraint("admin_unit_id", "oauth2_client_id"),)

    id = db.Column(db.Integer, primary_key=True)
    admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=True
    )
    oauth2_client_id = db.Column(
        db.Integer, db.ForeignKey("oauth2_client.id", ondelete="CASCADE"), nullable=True
    )
    permissions = db.Column(MutableList.as_mutable(AsaList()), nullable=True)


class AppKey(db.Model, TrackableMixin):
    __tablename__ = "app_key"
    __table_args__ = (UniqueConstraint("kid", "oauth2_client_id"),)

    id = db.Column(db.Integer, primary_key=True)
    admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=False
    )
    oauth2_client_id = db.Column(
        db.Integer,
        db.ForeignKey("oauth2_client.id", ondelete="CASCADE"),
        nullable=False,
    )
    checksum = db.Column(db.String(255), nullable=False)
    kid = db.Column(db.Unicode(255), index=True, nullable=False)
    public_key = db.Column(db.Text, nullable=False)

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
