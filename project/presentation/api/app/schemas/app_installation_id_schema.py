from project.presentation.api.app.schemas.app_installation_model_schema import (
    AppInstallationModelSchema,
)
from project.presentation.api.schemas import IdSchemaMixin


class AppInstallationIdSchema(AppInstallationModelSchema, IdSchemaMixin):
    pass
