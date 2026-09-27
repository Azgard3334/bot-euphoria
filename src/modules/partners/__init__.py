from .system import Partners
from .magazine import PRMagazine_Cog

async def setup(bot):
    await bot.add_cog(Partners(bot))
    await bot.add_cog(PRMagazine_Cog(bot))