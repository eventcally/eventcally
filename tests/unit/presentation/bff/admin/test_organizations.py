from project.application.commands import UpdateOrganizationAdminSettingsCommand
from project.presentation.bff.admin.organizations import OrganizationAdminSettingKey
from project.presentation.bff.admin.schemas import AdminOrganizationDetail


def test_setting_keys_match_the_command_and_schema():
    keys = {k.value for k in OrganizationAdminSettingKey}

    assert keys == set(UpdateOrganizationAdminSettingsCommand.model_fields) - {
        "actor",
        "id",
    }
    assert keys <= set(AdminOrganizationDetail.model_fields)
