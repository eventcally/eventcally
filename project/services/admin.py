from sqlalchemy import exists, func, update

from project import db
from project.models import Settings, User


def upsert_settings() -> Settings:
    result = Settings.query.first()
    if result is None:
        result = Settings()
        db.session.add(result)

    return result


def has_tos() -> bool:
    return db.session.scalar(
        exists().where(func.coalesce(Settings.tos, "") != "").select()
    )


def has_announcement() -> bool:
    return db.session.scalar(
        exists().where(func.coalesce(Settings.announcement, "") != "").select()
    )


def reset_tos_accepted_for_users():
    db.session.execute(update(User).values(tos_accepted_at=None))
    db.session.commit()
