from project.application.services.abstract_app_context_provider import (
    AbstractAppContextProvider,
)
from project.context import ContextProvider
from project.domain.models.entities.actor import Actor


class AppContextProvider(AbstractAppContextProvider):
    def __init__(self, context_provider: ContextProvider):
        self.context_provider = context_provider

    def get_current_actor(self) -> Actor:
        return self.context_provider.current_actor
