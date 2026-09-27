import re
import json
import discord
from discord import ui
from datetime import datetime, timedelta
from config import config

async def reset(bot):
    users = await bot.database.fetchall('SELECT * FROM partners_stats')

    start_week = (datetime.now() - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_week = start_week + timedelta(days=6)

    cont = ui.Container(accent_color=0xe6acfa)

    cont.add_item(ui.TextDisplay('## 🏁 Итоговая сводка за неделю'))
    cont.add_item(ui.TextDisplay(f'''
        > Период: **{start_week.strftime('%d.%m.%Y')} - {end_week.strftime('%d.%m.%Y')}**
        > Норма: **15**
        > Выполнили: **{len([user for user in users if user['week'] >= 15])}/{len(users)}**
    '''))

    cont.add_item(ui.Separator())

    cont.add_item(ui.TextDisplay('## Статистика персонала'))
    cont.add_item(ui.TextDisplay('-# Пользователь - за неделю - за всё время'))

    for user in users:
        cont.add_item(ui.TextDisplay(f'<@{user['id']}> - {user['week']} - {user['every']}'))

    cont.add_item(ui.Separator())

    cont.add_item(ui.TextDisplay(f'-# Обновлено в <t:{int(datetime.now().timestamp())}:f>'))

    view = ui.LayoutView()
    view.add_item(cont)

    await bot.database.execute('UPDATE partners_stats SET week = 0, links = "[]"')

    channel = await bot.fetch_channel(config['channels']['partners_bot_channel_id'])
    await channel.send(view=view, allowed_mentions=discord.AllowedMentions(users=[]))