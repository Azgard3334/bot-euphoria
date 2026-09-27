import os
import asyncio
from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from utils.database import Database
from utils.loggerManager import LoggerManager
from utils.scheduler import scheduler
from .staff_view import StaffView

load_dotenv()


def _role_id(name):
    try:
        return int(os.getenv(name, 0))
    except (TypeError, ValueError):
        return 0


class Staff(commands.Cog):
    staff = app_commands.Group(name='стафф', description='Статистика персонала')

    def __init__(self, bot):
        self.bot = bot
        self.logger = LoggerManager().get_logger('staff')
        self.support_role = _role_id('SUPPORT_ROLE_ID')
        self.moderator_role = _role_id('MODERATOR_ROLE_ID')
        self._stats = {}
        self._voice = {}
        self._dirty = set()

    async def cog_load(self):
        for command in self.get_app_commands():
            if command not in self.bot.tree.get_commands():
                self.bot.tree.add_command(command, guild=self.bot.guilds[0])
        await self.bot.tree.sync(guild=self.bot.guilds[0])
        scheduler.register(self.save_all, '23:59')
        try:
            await self._ensure_schema()
            await self.load_all()
        except Exception:
            pass

    async def _ensure_schema(self):
        await Database.execute(
            'CREATE TABLE IF NOT EXISTS staff_stats ('
            'id BIGINT PRIMARY KEY, '
            'messages INT NOT NULL DEFAULT 0, '
            'voice_seconds INT NOT NULL DEFAULT 0)'
        )

    async def load_all(self):
        rows = await Database.fetchall(
            'SELECT id, messages, voice_seconds FROM staff_stats'
        )
        for row in rows:
            self._stats[row['id']] = {
                'messages': int(row['messages'] or 0),
                'voice_seconds': int(row['voice_seconds'] or 0),
            }

    def _uid(self, uid):
        if uid not in self._stats:
            self._stats[uid] = {'messages': 0, 'voice_seconds': 0}
        return self._stats[uid]

    def _branch_of(self, member):
        role_ids = {r.id for r in member.roles}
        if self.moderator_role in role_ids:
            return 'moderator'
        if self.support_role in role_ids:
            return 'support'
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        member = getattr(message, 'member', None)
        if member is None or message.guild is None:
            return
        if self._branch_of(member) is None:
            return
        self._uid(message.author.id)['messages'] += 1
        self._dirty.add(message.author.id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or self._branch_of(member) is None:
            return
        self._track_voice(member.id, after.channel)

    def _track_voice(self, uid, channel):
        prev = self._voice.get(uid)
        now = datetime.now()
        if prev is not None:
            prev_channel, start = prev
            if channel is None or getattr(channel, 'id', None) != prev_channel:
                elapsed = int((now - start).total_seconds())
                if elapsed > 0:
                    self._uid(uid)['voice_seconds'] += elapsed
                    self._dirty.add(uid)
                self._voice.pop(uid, None)
        if channel is not None and uid not in self._voice:
            self._voice[uid] = (channel.id, now)

    def _flush_voice(self):
        for uid in list(self._voice.keys()):
            prev = self._voice.get(uid)
            if prev is None:
                continue
            channel_id, start = prev
            now = datetime.now()
            elapsed = int((now - start).total_seconds())
            if elapsed > 0:
                self._uid(uid)['voice_seconds'] += elapsed
                self._voice[uid] = (channel_id, now)
                self._dirty.add(uid)

    async def save_user(self, uid):
        stats = self._stats.get(uid)
        if stats is None:
            return
        try:
            await Database.execute(
                'INSERT INTO staff_stats (id, messages, voice_seconds) '
                'VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE '
                'messages = VALUES(messages), voice_seconds = VALUES(voice_seconds)',
                (uid, stats['messages'], stats['voice_seconds']),
            )
            self._dirty.discard(uid)
        except Exception:
            pass

    async def save_all(self):
        self._flush_voice()
        await asyncio.gather(*(self.save_user(uid) for uid in list(self._dirty)))

    def format_stats(self, branch):
        role_id = self.support_role if branch == 'support' else self.moderator_role
        rows = []
        for member in self.bot.get_all_members():
            if member.bot or role_id not in {r.id for r in member.roles}:
                continue
            stats = self._stats.get(member.id, {'messages': 0, 'voice_seconds': 0})
            rows.append((member.id, stats['messages'], stats['voice_seconds']))
        rows.sort(key=lambda r: r[1], reverse=True)
        lines = []
        for uid, msgs, vsecs in rows:
            member = self.bot.get_user(uid)
            name = member.display_name if member else f'<@{uid}>'
            lines.append(f'{name} — сообщения: {msgs}, голос: {self._fmt(vsecs)}')
        return self._chunk(lines)

    @staticmethod
    def _fmt(seconds):
        if seconds <= 0:
            return '—'
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f'{h:02d}:{m:02d}:{s:02d}'

    @staticmethod
    def _chunk(lines):
        if not lines:
            return ['Статистика пока пуста.']
        chunks = []
        buf = []
        total = 0
        for line in lines:
            if buf and total + len(line) + 1 > 1500:
                chunks.append('\n'.join(buf))
                buf = []
                total = 0
            buf.append(line)
            total += len(line) + 1
        if buf:
            chunks.append('\n'.join(buf))
        return chunks

    @staff.command(name='статистика', description='Статистика персонала по веткам')
    async def stats_command(self, interaction: discord.Interaction):
        self.logger.info(StaffView(self))
        try:
            await interaction.response.send_message(
                view=StaffView(self), ephemeral=True
            )
        except Exception as e:
            self.logger.error(e)
