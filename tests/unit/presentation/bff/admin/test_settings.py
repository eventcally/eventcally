from project.presentation.bff.admin.schemas import AdminSettings
from project.presentation.bff.admin.settings import SettingKey, _blank_to_none


def test_setting_keys_match_the_schema():
    assert {k.value for k in SettingKey} == set(AdminSettings.model_fields)


def test_blank_to_none():
    assert _blank_to_none(None) is None
    assert _blank_to_none("  \n") is None
    assert _blank_to_none(" <p>x</p> ") == " <p>x</p> "
