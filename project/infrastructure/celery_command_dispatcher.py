from project.application import commands
from project.application.abstract_command_dispatcher import AbstractCommandDispatcher


class CeleryCommandDispatcher(AbstractCommandDispatcher):
    def dispatch(self, command: commands.Command):
        from project.base_tasks import process_delayed_command

        command_class_path = (
            f"{command.__class__.__module__}.{command.__class__.__name__}"
        )
        command_dict = command.model_dump(exclude_unset=True)
        process_delayed_command.delay(command_class_path, command_dict)
