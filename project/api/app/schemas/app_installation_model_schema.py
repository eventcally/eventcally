from project.api.schemas import SQLAlchemyBaseSchema
from project.models import AppInstallation


class AppInstallationModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = AppInstallation
        load_instance = True
