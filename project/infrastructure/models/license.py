from project.infrastructure.extensions import db
from project.infrastructure.models.license_generated import LicenseGeneratedMixin


class License(db.Model, LicenseGeneratedMixin):
    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()
