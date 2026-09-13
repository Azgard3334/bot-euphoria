from .system import Staff


async def setup(bot):
    await bot.add_cog(Staff(bot))