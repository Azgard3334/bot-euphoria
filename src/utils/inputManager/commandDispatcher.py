from .iCommand import ICommand, ExitModuleCommand, LoadModuleCommand, ReloadModuleCommand, UnloadModuleCommand

class CommandDispatcher:
    def __init__(self, module_manager):
        self.commands = {
            'load': LoadModuleCommand(module_manager),
            'reload': ReloadModuleCommand(module_manager),
            'unload': UnloadModuleCommand(module_manager),
            'exit': ExitModuleCommand(module_manager),
        }

    def register_command(self, name: str, command: ICommand):
        result = 0
        if name in self.commands:
            result = 1
        else:
            self.commands[name] = command
        return result

    def remove_command(self, name: str):
        result = 0
        try:
            del self.commands[name]
        except KeyError:
            result = 1
        return result

    async def execute(self, command):
        if (command[0] not in self.commands):
            raise KeyError(command, self.commands[0])
        return await self.commands[command[0]].execute(command)
