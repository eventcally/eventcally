from project import rest_api, api_docs
from flask_apispec import marshal_with, doc
from flask_apispec.views import MethodResource
from project.api.organization.schemas import OrganizationSchema
from project.models import AdminUnit


class OrganizationResource(MethodResource):
    @doc(tags=["Organizations"])
    @marshal_with(OrganizationSchema)
    def get(self, id):
        return AdminUnit.query.get_or_404(id)


rest_api.add_resource(OrganizationResource, "/organizations/<int:id>")
api_docs.register(OrganizationResource)
