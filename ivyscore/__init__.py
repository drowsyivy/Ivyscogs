from .ivyscore import Ivyscore


def setup(bot):
    n = Ivyscore(bot)
    bot.add_cog(n)
