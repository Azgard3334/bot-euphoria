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
from utils.inputManager.event import Event

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='/', help_command=None, intents=discord.Intents.all())
        self.logger = LoggerManager().get_logger('bot')
        self._synced = False

    async def setup_hook(self):
        await Database.get_pool()
        self.logger.success('Database connected successfully')

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name='/help'),
            status=discord.Status.online
        )
        if not self._synced:
            await self.tree.sync()
            self._synced = True
            Event().running = True
            self.logger.success(f'Bot {self.user} started successfully')

    async def close(self):
        await Database.close()
        self.logger.info('Datebase connection closed')
        await super().close()
        self.logger.info('Bot stopped with exit code 0')

async def main():
    bot = Bot()
    module_manager = ModuleManager(bot)
    input_manager = InputManager(module_manager, '/tmp/fifo-bot')

    try:
        load_dotenv('.env')
        task = asyncio.create_task(input_manager.read())
        await bot.start(token=os.getenv('TOKEN'))
    except Exception as e:
        print(e) 
    finally:
        await task
        if not bot.is_closed():
            await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
