from project.api.schemas import PaginationRequestSchema, TrackableRequestSchemaMixin


class AppInstallationListRequestSchema(
    PaginationRequestSchema, TrackableRequestSchemaMixin
):
    pass
