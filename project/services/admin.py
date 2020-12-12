from project import db
from project.models import Settings


def upsert_settings():
    result = Settings.query.first()
    if result is None:
        result = Settings()
        db.session.add(result)

    return result
