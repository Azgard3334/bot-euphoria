import asyncio
import discord
from discord import ui
from discord.ext import commands
from pathlib import Path
from utils.loggerManager import LoggerManager

class Verification_View(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot:commands.Bot = bot
        self.logger = LoggerManager().get_logger('verification')

    async def interaction_check(self, interaction):
        return True

    @ui.button(emoji='🌸', style=discord.ButtonStyle.secondary, custom_id='cherry_blossom_button')
    async def cherry_blossom_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message('Кажется, ты выбрал не то эмодзи — верификация не пройдена.', ephemeral=True)

    @ui.button(emoji='🐻', style=discord.ButtonStyle.secondary, custom_id='bear_button')
    async def bear_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message('Кажется, ты выбрал не то эмодзи — верификация не пройдена.', ephemeral=True)
    
    @ui.button(emoji='🎀', style=discord.ButtonStyle.secondary, custom_id='ribbon_button')
    async def ribbon_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer()

        try:
            self.VERIFICATION_LOGS_CHANNEL:discord.TextChannel = discord.utils.find(lambda c: 'логи-верификации' in c.name, self.bot.guilds[0].channels)
            self.CHAT_CHANNEL:discord.TextChannel = discord.utils.find(lambda c: 'чатикс' in c.name, self.bot.guilds[0].channels)
            self.VERIFICATION_ROLE:discord.Role = discord.utils.find(lambda c: 'Не верифицированный' in c.name, self.bot.guilds[0].roles)
            self.MEMBER_ROLE:discord.Role = discord.utils.find(lambda c: 'Котик' in c.name, self.bot.guilds[0].roles)
            self.STAFF_ROLE:discord.Role = discord.utils.find(lambda c: 'Стафф' in c.name, self.bot.guilds[0].roles)
            self.PROGRAMMER_ROLE:discord.Role = discord.utils.find(lambda c: 'Программист' in c.name, self.bot.guilds[0].roles)

            if self.VERIFICATION_ROLE not in interaction.user.roles:
                await interaction.followup.send('Вы уже прошли верификацию!', ephemeral=True)
                return
            
            await interaction.user.remove_roles(self.VERIFICATION_ROLE)
            await interaction.user.add_roles(self.MEMBER_ROLE)

            view = ui.LayoutView()
            gallery = ui.MediaGallery(discord.MediaGalleryItem('attachment://welcome.png'))

            emoji = discord.utils.get(self.bot.guilds[0].emojis, name='omen_roles')
            container = ui.Container(accent_color=0xa96bc0)
            
            container.add_item(gallery)
            container.add_item(ui.Separator())

            container.add_item(ui.TextDisplay(f'## <@{interaction.user.id}>, **добро пожаловать!**'))
            container.add_item(ui.TextDisplay(f'> Мы искренне рады видеть тебя у нас. Наслаждайся общением, находи единомышленников и приятную компанию.  У нас уютная атмосфера - чувствуй себя как дома. Приятного времяпрепровождения на нашем сервере! {emoji if emoji else "❤️"}'))
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(f'-# {self.bot.guilds[0].name} • {self.STAFF_ROLE.mention}'))

            view.add_item(container)

            msg = await self.CHAT_CHANNEL.send(view=view, file=discord.File(f'{Path(__file__).parent}/img/welcome.png', filename='welcome.png'), allowed_mentions=discord.AllowedMentions(roles=True,users=False,everyone=False))
            emoji = discord.utils.get(self.bot.guilds[0].emojis, name='9061pinkribbon')

            await msg.add_reaction(emoji if emoji else '🪙')
            
            await self.VERIFICATION_LOGS_CHANNEL.send(f'Пользователь <@{interaction.user.id}> успешно прошел верификацию.')

            await asyncio.create_task(self.delete_message(msg))
        except Exception as e:
            await interaction.followup.send('Не удалось пройти верификацию. Попробуйте позже.', ephemeral=True)
            await self.VERIFICATION_LOGS_CHANNEL.send(f'{self.PROGRAMMER_ROLE.mention}\nПользователь <@{interaction.user.id}> не смог пройти верификацию.\nОшибка: {e}')
            self.logger.exception(f'Ошибка прохождения верефикации: {e}')
    
    async def delete_message(self, message: discord.Message):
        await asyncio.sleep(1200)
        await message.delete()