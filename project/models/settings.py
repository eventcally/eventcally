from project.extensions import db
from project.models.settings_generated import SettingsGeneratedMixin


class Settings(db.Model, SettingsGeneratedMixin):
    pass
