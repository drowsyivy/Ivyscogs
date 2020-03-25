from .ficutils import Ficutils


def setup(bot):
    n = Ficutils(bot)
    bot.add_cog(n)
