import os
import asyncio
import traceback

from .event import Event
from utils.loggerManager import LoggerManager
from .commandDispatcher import CommandDispatcher

class InputManager:
    def __init__(self, module_manager, init_file):
        self.command_dispatcher = CommandDispatcher(module_manager)
        self.file = init_file

    def _creat(self):
        if not os.path.exists(self.file):
            os.mkfifo(self.file, 0o666)

    def _read(self):
        with open(self.file, 'r', encoding='utf-8') as f:
             return f.readline().strip()

    def _write(self, message):
        with open(self.file, 'w', encoding='utf-8') as f:
            f.write(f'{message}\n')

    async def read(self):
        self._creat()

        while not Event().running:
            await asyncio.sleep(1)
        await asyncio.to_thread(self._write, 'Bot started successfully')

        while Event().running:
            try:
                data = (await asyncio.to_thread(self._read)).split()
                result = await self.command_dispatcher.execute(data)
                await asyncio.to_thread(self._write, result)
            except OSError as e:
                self._creat()
            except Exception as e:
                await asyncio.to_thread(self._write, traceback.format_exc())
 
        os.unlink(self.file)
