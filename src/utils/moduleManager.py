from discord.ext import commands
from utils.loggerManager import LoggerManager


class ModuleManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = LoggerManager().get_logger('bot')

    async def _manage(self, action, name: str, success_message: str):
        result = False
        try:
            print(name)
            await action(name)
            self.logger.success(success_message)
        except Exception as e: #commands.ExtensionError
            self.logger.error(f'failed to control module {name}:\n{e}')
            result = True
        return result

    async def load(self, name: str):
        return await self._manage(
                self.bot.load_extension,
                name,
                f'{name} is loaded'
            )

    async def unload(self, name: str):
        return await self._manage(
            self.bot.unload_extension,
            name,
            f'{name} is unloaded'
        )

    async def reload(self, name: str):
        return await self._manage(
            self.bot.reload_extension,
            name,
            f'{name} is reloaded'
        )

    async def exit(self):
        await self.bot.close()
