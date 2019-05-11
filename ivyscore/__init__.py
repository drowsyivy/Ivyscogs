from .ivyscore import Ivyscore


def setup(bot):
    n = Ivyscore()
    bot.add_cog(n)
