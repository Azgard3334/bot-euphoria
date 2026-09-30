import os
import asyncio
from .event import Event
from utils.loggerManager import LoggerManager
from .commandDispatcher import CommandDispatcher


class InputManager:
    def __init__(self, module_manager, init_file):
        self.command_dispatcher = CommandDispatcher(module_manager)
        self.file = init_file

    def _creat(self):
        if not os.path.exists(self.file):
            os.mkfifo(file, 0o666)

    def _read(self):
        with open(self.file, 'r', encoding='utf-8') as f:
             return f.readline().strip()

    def _write(self, message):
        with open(self.file, 'w', encoding='utf-8') as f:
            f.write(message)

    async def read(self):
        self._creat()

        while Event().running:
            try:
                data = (await asyncio.to_thread(self._readline, file)).split()
                result = await self.command_dispatcher.execute(data)
                self._write(result)
            except OSError as e:
                self._creat()
 
        os.unlink(file)
