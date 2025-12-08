from typing import Generic, Type, TypeVar

from flask_sqlalchemy import SQLAlchemy

# Define a generic type variable for the model
TModel = TypeVar("TModel")


class BaseRepo(Generic[TModel]):
    model_class: Type[TModel]

    def __init__(self, db: SQLAlchemy, **kwargs):
        self.db = db

    def get_object_by_id(self, object_id) -> TModel:
        return self.db.session.query(self.model_class).get(object_id)

    def insert_object(self, object: TModel) -> TModel:
        self.db.session.add(object)
        self.db.session.commit()

    def update_object(self, object: TModel):
        self.db.session.commit()

    def delete_object(self, object: TModel) -> TModel:
        self.db.session.delete(object)
        self.db.session.commit()
