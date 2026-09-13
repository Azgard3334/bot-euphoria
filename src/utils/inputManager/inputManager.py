import os
import asyncio
from .event import Event
from utils.loggerManager import LoggerManager
from .commandDispatcher import CommandDispatcher


class InputManager:
    def __init__(self, module_manager):
        self.sources: list[InputSource] = list()
        self.command_dispatcher = CommandDispatcher(module_manager)
        self.logger = LoggerManager().get_logger('bot')

    @staticmethod
    def _readline(file):
        with open(file, 'r') as f:
             return f.readline().strip()

    def _create_fifo(self, name):
        os.mkfifo(name, 0o666)
        self.logger.success(f'Create {name} file')

    async def read(self, file: str):
        try:
            if not os.path.exists(file):
                self._create_fifo(file)
        except Exception as e:
            self.logger.exception(e)
            Event.running = False

        while Event().running:
            try:
                data = await asyncio.to_thread(self._readline, file)
                data = data.split()
                info = await self.command_dispatcher.execute(data)
                self.logger.info(info)
            except OSError as e:
                self.logger.error(e)
                Event().running = False
            except Exception as e:
                self.logger.exception(e)
        os.unlink(file)
        self.logger.success(f'{file} has been deleted')

        return 0
