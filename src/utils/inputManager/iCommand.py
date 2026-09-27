from abc import ABC, abstractmethod
from .event import Event

class ICommand(ABC):
    @abstractmethod
    async def execute(self, *args):
        pass

class LoadModuleCommand(ICommand):
    def __init__(self, module_manager):
        self.module_manager: ModuleManager = module_manager

    async def execute(self, module_name):
        return await self.module_manager.load(module_name[0])

class ReloadModuleCommand(ICommand):
    def __init__(self, module_manager):
        self.module_manager: ModuleManager = module_manager

    async def execute(self, module_name):
        return await self.module_manager.reload(module_name[0])

class UnloadModuleCommand(ICommand):
    def __init__(self, module_manager):
        self.module_manager: ModuleManager = module_manager

    async def execute(self, module_name):
        return await self.module_manager.unload(module_name[0])

class ExitModuleCommand(ICommand):
    def __init__(self, module_manager):
        self.module_manager: ModuleManager = module_manager

    async def execute(self, command):
        Event().running = False
        await self.module_manager.exit()
