from typing import Generic, Type, TypeVar

from project.context import ContextProvider
from project.repos.base_repo import BaseRepo

# Define a generic type variable for the model
TModel = TypeVar("TModel")


class BaseService(Generic[TModel]):
    model_class: Type[TModel]

    def __init__(
        self, repo: BaseRepo[TModel], context_provider: ContextProvider, **kwargs
    ):
        self.repo = repo
        self.context_provider = context_provider

    def get_object_by_id(self, object_id) -> TModel:  # pragma: no cover
        return self.repo.get_object_by_id(object_id)

    def insert_object(self, object: TModel) -> TModel:
        self.repo.insert_object(object)

    def update_object(self, object: TModel):
        self.repo.update_object(object)

    def delete_object(self, object: TModel) -> TModel:
        self.repo.delete_object(object)
