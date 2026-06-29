from project.application import commands
from project.application.abstract_command_dispatcher import AbstractCommandDispatcher


class CeleryCommandDispatcher(AbstractCommandDispatcher):
    def dispatch(self, command: commands.Command):
        from project.base_tasks import process_delayed_command_v2

        command_class_path = (
            f"{command.__class__.__module__}.{command.__class__.__name__}"
        )
        command_json = command.model_dump_json(exclude_unset=True)
        process_delayed_command_v2.delay(command_class_path, command_json)
