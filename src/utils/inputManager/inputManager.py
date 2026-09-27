import os
import asyncio
from .event import Event
from utils.loggerManager import LoggerManager
from .commandDispatcher import CommandDispatcher


class InputManager:
    def __init__(self, module_manager):
        self.command_dispatcher = CommandDispatcher(module_manager)
        self.logger = LoggerManager().get_logger('bot')

    @staticmethod
    def _readline(file):
        with open(file, 'r') as f:
             return f.readline().strip()

    async def read(self, file: str):
        try:
            if not os.path.exists(file):
                os.mkfifo(file, 0o666)

            while Event().running:
                data = (await asyncio.to_thread(self._readline, file)).split()
                info = await self.command_dispatcher.execute(data)
        except OSError as e:
            self.logger.error("failed to read file: file was remove")
            Event().running = False 
        
        os.unlink(file)

        return 0
