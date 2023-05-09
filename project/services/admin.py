from sqlalchemy import exists, func

from project import db
from project.models import Settings


def upsert_settings():
    result = Settings.query.first()
    if result is None:
        result = Settings()
        db.session.add(result)

    return result


def has_tos():
    return db.session.scalar(
        exists().where(func.coalesce(Settings.tos, "") != "").select()
    )
