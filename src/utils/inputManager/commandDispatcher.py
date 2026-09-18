from .iCommand import *
from utils.loggerManager import LoggerManager

class CommandDispatcher:
    def __init__(self, module_manager):
        self.commands = {
            'load': LoadModuleCommand(module_manager),
            'reload': ReloadModuleCommand(module_manager),
            'unload': UnloadModuleCommand(module_manager),
            'exit': ExitModuleCommand(module_manager),
        }
        self.logger = LoggerManager().get_logger('bot')

    def register(self, name: str, command: ICommand):
        result: bool = False
        if name in self.commands:
            result = True
        else:
            self.commands[name] = command
        return result

    def remove(self, name: str):
        result: bool = False
        try:
            del self.commands[name]
        except KeyError:
            result = True
        return result

    async def execute(self, command):
        if (command[0] not in self.commands):
            self.logger.error(f'{command} is not exist')
        return await self.commands[command[0]].execute(command)
