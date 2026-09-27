import time
import asyncio
import discord
from discord import ui
from discord.ext import commands
from datetime import datetime, timedelta

class PRMagazine_View(ui.LayoutView):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def create_view(self, interaction: discord.Interaction):
        user = await self.bot.database.get(interaction.user.id, 'partners_stats')
        container = ui.Container(accent_color=0xe6acfa)

        container.add_item(ui.TextDisplay('### :newspaper: Информация'))
        container.add_item(ui.TextDisplay(f'Ваши баллы: **{user['score']}**'))

        container.add_item(ui.Separator())

        container.add_item(ui.TextDisplay('### Текст рекламы:'))
        container.add_item(ui.TextDisplay(user['text'] or 'Тут пусто..'))

        container.add_item(ui.Separator())

        row1 = ui.ActionRow()
        row1.add_item(ui.Select(custom_id='partner_ads_type', placeholder='Выберите тип рекламы', options=[
            discord.SelectOption(label='Реклама без пинга | 50', value='50', emoji='💸'),
            discord.SelectOption(label='Реклама с пингом here | 100', value='100', emoji='💸'),
            discord.SelectOption(label='Реклама с пингом everyone | 150', value='150', emoji='💸')
        ]))

        row2 = ui.ActionRow()
        row2.add_item(ui.Button(style=discord.ButtonStyle.green, label='Опубликовать рекламу', emoji='📢', custom_id='partner_publish'))
        row2.add_item(ui.Button(style=discord.ButtonStyle.gray, label='Изменить текст рекламы', emoji='✏️', custom_id='partner_edit'))

        container.add_item(row1)
        container.add_item(row2)

        self.add_item(container)

class PRMagazine_Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.views = {}
        self.ADS_CHANNEL_ID = 1542978035303587850
    
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        id = interaction.data.get('custom_id')

        if id == 'partner_ads_type':
            self.views[interaction.user.id] = interaction.data.get('values')[0]
            await interaction.response.defer()

        if id == 'partner_edit':
            user = await self.bot.database.get(interaction.user.id, 'partners_stats')

            class EditTextModal(ui.Modal, title='Изменение текста'):
                inputText = ui.TextInput(
                    label='Текст рекламы',
                    placeholder='Введите ваш текст..',
                    default=user['text'],
                    style=discord.TextStyle.paragraph,
                    max_length=2000
                )

                async def on_submit(self, modal_interaction):
                    await self.bot.database.set(modal_interaction.user.id, {'text':self.inputText.value}, 'partners_stats')

                    view = PRMagazine_View(self.bot)
                    await view.create_view(modal_interaction)

                    await modal_interaction.response.edit_message(view=view)

            await interaction.response.send_modal(EditTextModal())

        if id == 'partner_publish':
            await interaction.response.defer(thinking=True, ephemeral=True)

            user = await self.bot.database.get(interaction.user.id, 'partners_stats')

            if interaction.user.id not in self.views.keys():
                await interaction.followup.send(':x: Сначала выберите цену рекламы.',)
                return

            price = int(self.views[interaction.user.id])
            allowed = None
            text = user['text']
            text = text.replace('@here', '').replace('@everyone', '')

            if 1 != 1:
                await interaction.followup.send(':x: Сегодня публиковать рекламу нельзя. Попробуйте завтра.')
                return

            hour = (datetime.now() + timedelta(hours=3)).hour
            if hour < 12 or hour > 20:
                await interaction.followup.send(':x: Публиковать рекламу возможно только с 12-20 МСК')
                return
            
            if user['timeout'] is not None and datetime.now() < user['timeout']:
                await interaction.followup.send(':x: Таймаут с прошлой рекламы не прошёл.')
                return
            
            if user['score'] < price:
                await interaction.followup.send(':x: У вас недостаточно монет для публикации рекламы.')
                return

            if price == 50:
                allowed = discord.AllowedMentions(users=[],roles=[],everyone=False)
            elif price == 100:
                text = '||@here||\n' + text
                allowed = discord.AllowedMentions(users=[],roles=[],everyone=False)
            else:
                text = '||@everyone||\n' + text
                allowed = discord.AllowedMentions(users=[],roles=[],everyone=True)

            channel = await self.bot.fetch_channel(self.ADS_CHANNEL_ID)
            await channel.send(text, allowed_mentions=allowed)

            del self.views[interaction.user.id]

            await interaction.followup.send(':white_check_mark: Реклама успешно опубликована.')

            await self.bot.database.set(interaction.user.id, {'score': user['score']-price, 'timeout':datetime.now() + timedelta(weeks=2)}, 'partners_stats')