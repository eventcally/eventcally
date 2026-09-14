import pytest


def test_write_id_schema_mixin_raises_on_unknown_reference(app, db):
    from marshmallow import ValidationError

    from project.api.license.schemas import LicenseWriteIdSchema

    with app.app_context():
        with pytest.raises(ValidationError):
            LicenseWriteIdSchema().load({"id": 999999})
