from datetime import datetime

from project.application.read_models.image_read_model import ImageReadModel


def test_get_hash_matches_trackable_mixin():
    image = ImageReadModel(id=1, last_modified_at=datetime(2026, 1, 2, 8, 30))

    # Same value TrackableMixin.get_hash produces (milliseconds, GMT).
    assert image.get_hash() == 1767342600000


def test_get_hash_without_timestamp():
    assert ImageReadModel(id=1).get_hash() == 0
