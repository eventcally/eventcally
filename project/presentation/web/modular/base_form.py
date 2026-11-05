from flask_wtf import FlaskForm

from project.domain.models.entities.actor import Actor


class BaseForm(FlaskForm):
    def get_current_actor(self) -> Actor:
        from flask import current_app

        return current_app.container.context.context_provider().current_actor
