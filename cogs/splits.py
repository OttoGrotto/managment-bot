from discord.ext import commands
import discord
from .resources import Database

class Splits(commands.Cog):

    def __init__(self, bot) -> None:
        ...

def setup(client: discord.Bot):
    client.add_cog(Splits(client))