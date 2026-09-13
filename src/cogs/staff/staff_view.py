import discord
from discord import ui


class StaffView(ui.LayoutView):
    def __init__(self, cog, mode='menu', branch=None):
        super().__init__(timeout=180)
        self.cog = cog
        self.mode = mode
        self.branch = branch
        self._build()

    def _build(self):
        container = ui.Container()
        if self.mode == 'menu':
            container.add_item(
                ui.TextDisplay('Выберите какую ветку вы хотите посмотреть')
            )
            row = ui.ActionRow()
            supports = ui.Button(
                label='Саппорты',
                style=discord.ButtonStyle.secondary,
                custom_id='staff_supports',
            )
            supports.callback = self.show_supports
            row.add_item(supports)
            moderators = ui.Button(
                label='Модераторы',
                style=discord.ButtonStyle.secondary,
                custom_id='staff_moderators',
            )
            moderators.callback = self.show_moderators
            row.add_item(moderators)
            container.add_item(row)
        else:
            for line in self.cog.format_stats(self.branch):
                container.add_item(ui.TextDisplay(line))
            row = ui.ActionRow()
            back = ui.Button(
                label='Назад',
                style=discord.ButtonStyle.secondary,
                custom_id='staff_back',
            )
            back.callback = self.show_menu
            row.add_item(back)
            container.add_item(row)
        self.add_item(container)

    async def show_supports(self, interaction):
        await self._switch(interaction, 'support')

    async def show_moderators(self, interaction):
        await self._switch(interaction, 'moderator')

    async def show_menu(self, interaction):
        await interaction.response.edit_message(view=StaffView(self.cog))

    async def _switch(self, interaction, branch):
        await interaction.response.edit_message(
            view=StaffView(self.cog, mode='stats', branch=branch)
        )