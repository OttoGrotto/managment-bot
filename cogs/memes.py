import discord
from discord.ext import commands
import random
import datetime
from .resources import Database as db

db = db()
class ChannelException(BaseException): ...

class Memes(commands.Cog):
    def __init__(self, client) -> None:
        self.client = client

    @commands.command(name="daily", description="Get your daily reward!")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx: discord.ApplicationContext, rig: str = None):
        if ctx.channel.id == 1146966722566443008:
            randint = 48 if rig == "rig" and ctx.author.id == 201850930121932801 else random.randint(1, 100)
            if randint == 48:
                embed = discord.Embed(title="Daily Reward", description="You have claimed your daily reward!\nOf 20m coins, please ping <@201850930121932801>", color=discord.Color.green())
                embed.set_footer(text="Fyre Bot - Daily")
                embed.set_thumbnail(url=ctx.guild.icon.url)
                await ctx.channel.send(embed=embed)
            else:
                embed = discord.Embed(title="Daily Reward", description=f"You have claimed your daily reward!\nOf absolutely nothing, please try again later :)", color=discord.Color.green())
                embed.set_footer(text="Fyre Bot - Daily")
                embed.set_thumbnail(url=ctx.guild.icon.url)
                await ctx.channel.send(embed=embed)
        else:
            raise ChannelException("You can only use this command in <#1146966722566443008>")

    @daily.error
    async def daily_on_error(self, ctx: discord.ApplicationContext, error):
        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.timedelta(seconds=round(error.retry_after))
            time = str(time).split(":")
            time = f"{time[0]}h {time[1]}m {time[2]}s"
            embed = discord.Embed(title="Daily Reward", description=f"You have already claimed your daily reward!\nTry again in {time}", color=discord.Color.red())
            embed.set_footer(text="Fyre Bot - Daily")
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.channel.send(embed=embed)
        elif isinstance(error, ChannelException):
            error = str(error).split(":")[-1]
            embed = discord.Embed(title="Daily Reward", description=f"{error}", color=discord.Color.red())
            embed.set_footer(text="Fyre Bot - Daily")
            embed.set_image(url=ctx.guild.icon.url)
            await ctx.channel.send(embed=embed)
            ctx.command.reset_cooldown(ctx)

def setup(client: discord.Bot):
    client.add_cog(Memes(client))