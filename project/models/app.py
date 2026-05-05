from project.domain.commands.install_app_command import InstallAppCommand
from project.domain.commands.uninstall_app_command import UninstallAppCommand
from project.domain.commands.update_app_installation_permissions_command import (
    UpdateAppInstallationPermissionsCommand,
)
from project.domain.events import (
    AppInstallationCreated,
    AppInstallationPermissionsUpdated,
    AppUninstalled,
)
from project.extensions import db
from project.models.app_installation_generated import AppInstallationGeneratedMixin
from project.models.app_key_generated import AppKeyGeneratedMixin


class AppInstallation(db.Model, AppInstallationGeneratedMixin):
    @classmethod
    def create_installation(cls, cmd: InstallAppCommand, app) -> "AppInstallation":
        instance = cls()
        instance.admin_unit_id = cmd.admin_unit_id
        instance.oauth2_client_id = app.id
        instance.permissions = app.app_permissions
        instance.domain_events.append(
            AppInstallationCreated(
                actor=cmd.actor,
                id=-1,
                admin_unit_id=instance.admin_unit_id,
                app_id=instance.oauth2_client_id,
                permissions=instance.permissions,
            )
        )
        return instance

    def update_permissions(self, cmd: UpdateAppInstallationPermissionsCommand):
        self.permissions = cmd.permissions
        self.domain_events.append(
            AppInstallationPermissionsUpdated(
                actor=cmd.actor,
                id=self.id,
                admin_unit_id=self.admin_unit_id,
                app_id=self.oauth2_client_id,
                permissions=self.permissions,
            )
        )

    def uninstall(self, cmd: UninstallAppCommand):
        self.domain_events.append(
            AppUninstalled(
                actor=cmd.actor,
                id=self.id,
                admin_unit_id=self.admin_unit_id,
                app_id=self.oauth2_client_id,
            )
        )


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
