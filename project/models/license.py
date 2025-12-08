from project import db
from project.models.license_generated import LicenseGeneratedMixin


class License(db.Model, LicenseGeneratedMixin):
    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()
