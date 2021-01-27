from project.api import add_api_resource
from flask_apispec import marshal_with, doc
from project.api.resources import BaseResource
from project.api.schemas import NoneSchema
from project.api.dump.schemas import DumpResponseSchema


class DumpResource(BaseResource):
    @doc(
        summary="Dump model definition",
        description="Always returns 404 because the endpoint is just for response definition of the dump data file. Go to the developers page to learn how to download the dump data file.",
        tags=["Dump"],
    )
    @marshal_with(NoneSchema, 404)
    @marshal_with(DumpResponseSchema, 200)
    def get(self, **kwargs):
        return None, 404


add_api_resource(DumpResource, "/dump", "api_v1_dump")
