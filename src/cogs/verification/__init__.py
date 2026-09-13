from .system import Verification

async def setup(bot):
    await bot.add_cog(Verification(bot))