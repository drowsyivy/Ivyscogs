from .ivyutils import Ivyutils


def setup(bot):
    n = Ivyutils(bot)
    bot.add_cog(n)
