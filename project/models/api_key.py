from sqlalchemy import CheckConstraint, UniqueConstraint

from project import db
from project.models.trackable_mixin import TrackableMixin


class ApiKey(db.Model, TrackableMixin):
    __tablename__ = "apikey"
    __display_name__ = "API key"
    __table_args__ = (
        CheckConstraint(
            "(admin_unit_id IS NULL) <> (user_id IS NULL)",
            name="apikey_admin_unit_xor_user",
        ),
        UniqueConstraint("name", "admin_unit_id", name="uq_apikey_name_admin_unit_id"),
        UniqueConstraint("name", "user_id", name="uq_apikey_name_user_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False, unique=True)

    admin_unit_id = db.Column(
        db.Integer, db.ForeignKey("adminunit.id", ondelete="CASCADE"), nullable=True
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )

    def generate_key(self) -> str:
        from project.utils import generate_api_key, hash_api_key

        key = generate_api_key()
        self.key_hash = hash_api_key(key)
        return key
