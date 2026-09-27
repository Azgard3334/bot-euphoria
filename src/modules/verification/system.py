import discord
from discord.ext import commands
from .verification_view import Verification_View
from utils.managerPermission import ManagerPermission
from pathlib import Path
from utils.loggerManager import LoggerManager

class Verification(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.view = Verification_View(self.bot)
        self.logger = LoggerManager().create_logger('verification')
        self.bot.add_view(self.view)

    async def cog_unload(self):
        self.view.stop()
    
    @commands.command('verificationHERE')
    @ManagerPermission.is_owner()
    async def send_verification_view(self, ctx: commands.Context):
        try:
            await ctx.message.delete()

            embed = discord.Embed(
                title='Верификация',
                description='Для безопасности нашего сервера и исключения ботов, пожалуйста, пройдите капчу. Сразу после прохождения вы сможете свободно пользоваться сервером.\n\n**Для прохождения нажмите на бантик:**',
                color=discord.Color.dark_purple()
            )
            file = discord.File(f'{Path(__file__).parent}/img/verification.png', filename='verification.png')
            embed.set_image(url='attachment://verification.png')

            await ctx.send(embed=embed, view=self.view, file=file)
        except Exception as e:
            self.logger.error(f'Ошибка : {e}')