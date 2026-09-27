import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

from utils.database import Database
from utils.scheduler import scheduler
from utils.loggerManager import LoggerManager
from utils.inputManager.inputManager import InputManager
from utils.moduleManager import ModuleManager

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', help_command=None, intents=discord.Intents.all())
        self.logger = LoggerManager().get_logger('bot')
        self._synced = False

    async def setup_hook(self):
        await Database.get_pool()

    async def on_ready(self):
        self.logger.success(f'Бот {self.user} готов к работе')
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name='/help'),
            status=discord.Status.online
        )
        if not self._synced:
            await self.tree.sync()
            self._synced = True

    async def close(self):
        await Database.close()
        await super().close()

async def main():
    logger = LoggerManager().get_logger('bot')
    bot = Bot()
    module_manager = ModuleManager(bot)
    input_manager = InputManager(module_manager)

    task = asyncio.create_task(input_manager.read('tmp/fifo'))

    try:
        load_dotenv('.env')
        await bot.start(token=os.getenv('TOKEN'))
        print("bot stoped")
    except KeyboardInterrupt:
        logger.warning('Бот остановлен пользователем')
    except Exception as e:
        logger.exception(f'Произошла ошибка при запуске: {e}')
    finally:
        await task
        if not bot.is_closed():
            await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
