import re
import json
import discord
from discord import app_commands, ui
from discord.ext import commands
from .magazine import PRMagazine_View
from utils.database import Database
from utils.managerPermission import ManagerPermission
from datetime import datetime

class Partners(commands.Cog):
    group = app_commands.Group(name='партнеры', description='Статистика PR-менеджеров')

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.PARTNER_ROLE = self.bot.guilds[0].get_role(1542452446033481829)
        self.PARTNERS_CHANNEL_ID = 1541935060381474927
        self.PARTNERS_CHANNEL_BOT_ID = 1542452850335031316
    
    async def cog_load(self):
        for command in self.get_app_commands():
            if command not in self.bot.tree.get_commands():
                self.bot.tree.add_command(command, guild=self.bot.guilds[0])
        
        await self.bot.tree.sync(guild=self.bot.guilds[0])

        await Database.execute(f'''
            CREATE TABLE IF NOT EXISTS `partners_stats` (
                `id` bigint(20) NOT NULL,
                `week` int(10) NOT NULL DEFAULT 0,
                `every` int(10) NOT NULL DEFAULT 0,
                `links` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '[]' CHECK (json_valid(`links`)),
                `score` int(10) NOT NULL DEFAULT 0,
                `text` text NOT NULL DEFAULT '',
                `timeout` datetime DEFAULT NULL,
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
        ''')

# Отправка рекламы

    def find_link(self, text: str) -> json:
        try:
            pattern = r'(https?:\/\/)?(www\.)?(discord\.(gg|com\/invite)\/[a-zA-Z0-9]+)'
            result = re.findall(pattern, text)

            links = list(set([match[2] for match in result]))
            return links[0]
        except:
            return []

    def find_image(self, text: str) -> json:
        try:
            pattern = r'https?://[^\s]+?\.(?:jpg|jpeg|png|gif|webp|bmp|svg|ico)(?:\?[^\s]*)?'
            result = re.findall(pattern, text, re.IGNORECASE)

            return result
        except:
            return []

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.channel.id != self.PARTNERS_CHANNEL_ID:
            return

        url = self.find_link(message.content)
        global_url = url

        if url == []:
            await message.channel.send(':x: Вы не указали ссылку на сервер.')
            return

        user = await Database.get(message.author.id, 'partners_stats')

        if url in json.loads(user['links']):
            await message.channel.send(':x: Вы уже заключали партнёрство с данным сервером сегодня.')
            return

        url = await self.bot.fetch_invite(url)
        
        if url.guild.id == message.guild.id:
            await message.channel.send(':x: Нельзя заключать партнёрство с данным сервером.')
            return

        imgs = self.find_image(message.content)
        container = ui.Container(accent_color=0xe6acfa)

        container.add_item(ui.TextDisplay(':notepad_spiral: **Партнёрство заключено. :white_check_mark:**'))

        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay(message.content))

        if len(imgs) > 0:
            gallery = ui.MediaGallery(*(discord.MediaGalleryItem(img) for img in imgs))
            container.add_item(gallery)

        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay('## **Сервер**'))
        container.add_item(ui.TextDisplay(f':label: Название сервера: {url.guild.name}'))
        container.add_item(ui.TextDisplay(f':busts_in_silhouette: Количество участников: {url.approximate_member_count}'))
        container.add_item(ui.TextDisplay('## **Менеджер:**'))
        container.add_item(ui.TextDisplay(f':bust_in_silhouette: {message.author.mention}'))
        container.add_item(ui.TextDisplay(f':calendar_spiral: Партнёрств на этой неделе: {user['week']}'))
        container.add_item(ui.TextDisplay(f':handshake: Общее количество партнёрств: {user['every']}'))

        view = ui.LayoutView()
        view.add_item(container)
        
        channel = await self.bot.fetch_channel(self.PARTNERS_CHANNEL_BOT_ID)
        await channel.send(view=view, allowed_mentions=discord.AllowedMentions(users=[]))
        
        await Database.set(message.author.id, {'week': user['week'] + 1, 'every': user['every'] + 1, 'links': json.dumps(json.loads(user['links']) + [global_url])}, 'partners_stats')

# Команды

    @group.command(name='статистика', description='Статистика PR-менеджеров.')
    async def stats(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if self.PARTNER_ROLE not in interaction.user.roles:
            await interaction.followup.send('Вы не PR-менеджер!')
            return

        users = await Database.fetchall('SELECT id, week, every FROM partners_stats')
        cont = ui.Container(accent_color=0xe6acfa)

        cont.add_item(ui.TextDisplay('## Статистика персонала'))
        cont.add_item(ui.TextDisplay('-# Пользователь - за неделю - за всё время'))
    
        for user in users:
            cont.add_item(ui.TextDisplay(f'<@{user['id']}> - {user['week']} - {user['every']}'))
    
        cont.add_item(ui.Separator())
    
        cont.add_item(ui.TextDisplay(f'-# Обновлено в <t:{int(datetime.now().timestamp())}:f>'))
    
        view = ui.LayoutView()
        view.add_item(cont)
    
        await interaction.followup.send(view=view, allowed_mentions=discord.AllowedMentions(users=[]))

    @group.command(name='магазин', description='Магазин PR-менеджеров.')
    async def magazine(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if self.PARTNER_ROLE not in interaction.user.roles:
            await interaction.followup.send('Вы не PR-менеджер!')
            return

        view = PRMagazine_View()
        await view.create_view(interaction)

        await interaction.followup.send(view=view)

    @group.command(name='выдать', description='Выдать PR-менеджера.')
    @app_commands.describe(member='Пользователь')
    async def add_manager(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)

        if self.PARTNER_ROLE in member.roles:
            await interaction.followup.send(f'У пользователя {member.mention} уже есть роль PR-менеджера.', allowed_mentions=discord.AllowedMentions(users=[]))
            return

        await member.add_roles(self.PARTNER_ROLE)
        await Database.add(member.id, {}, 'partners_stats')

        await interaction.followup.send(f'{member.mention} добавлен в PR-менеджеры.', allowed_mentions=discord.AllowedMentions(users=[]))

    @group.command(name='убрать', description='Убрать PR-менеджера.')
    @app_commands.describe(member='Пользователь')
    async def delete_manager(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.defer(ephemeral=True)

        if self.PARTNER_ROLE not in member.roles:
            await interaction.followup.send(f'У пользователя {member.mention} нет роли PR-менеджера.', allowed_mentions=discord.AllowedMentions(users=[]))
            return

        await member.remove_roles(self.PARTNER_ROLE)
        await Database.delete(member.id, 'partners_stats')

        await interaction.followup.send(f'{member.mention} удалён из PR-менеджеров.', allowed_mentions=discord.AllowedMentions(users=[]))
    
    @group.command(name='reset', description='test reset')
    async def test_reset(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            from .reset import reset
            await reset(self.bot, self.PARTNERS_CHANNEL_BOT_ID)
        except Exception as e:
            await interaction.followup.send(str(e))