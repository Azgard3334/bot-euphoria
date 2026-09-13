from discord.ext import commands
from utils.loggerManager import LoggerManager


class ModuleManager:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = LoggerManager().get_logger('module_manager')

    async def _manage(self, action, name: str, success_message: str):
        info = success_message
        try:
            await action(name)
            self.logger.success(success_message)
        except commands.ExtensionError as e:
            info = str(e)
            self.logger.error(f'Ошибка управления модулем {name}: {e}')
        return info

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
