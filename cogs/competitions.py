import discord, os
from discord.utils import get
from discord.ext import commands, tasks
from discord.ui.item import Item
from wom.client import Client as c
from datetime import datetime, timedelta

_COMPETITIONS = c(os.getenv("wiseoldman_API_KEY"))

class codeModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value = None
        self.add_item(discord.ui.InputText(label='Verification code', placeholder='Verification code', custom_id='code'))

    async def callback(self, interaction: discord.Interaction):
        print(interaction.custom_id)
        if interaction.custom_id == 'submit':
            print(self.children[0].value)
            self.value = self.children[0].value
            await interaction.response.send_message('Verification code submitted.', ephemeral=True)
            self.stop()
            return self.value
        elif interaction.custom_id == 'cancel':
            await interaction.response.send_message('Cancelled', ephemeral=True)
            self.stop()
            return

class Competitions(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot: discord.Bot = bot
        print(f'{self.__cog_name__} is ready.')
        self.WOM: c = _COMPETITIONS

    competitions = discord.SlashCommandGroup(name='competitions', description='Commands for competitions.')

    @competitions.command(aliases=['lb', 'top'], description='Get the top 10 of a competition.')
    async def leaderboard(self, ctx: discord.context.ApplicationContext, id: discord.Option(int, description='If you want to see a specific competition', required=False) = None):
        print("Getting top 10...")
        await self.WOM.start()
        if id == None:
            print('No id provided, aborting.')
            embed = discord.Embed(title='ERROR', description='No id provided, please provide an id.')
            await ctx.respond(embed=embed)
            return
        await ctx.send_response(f'Getting competition {id}...', delete_after=5)
        await self.WOM.competitions.update_outdated_participants(id=id, verification_code=os.getenv('GROUP_VERIFICATION_CODE'))
        compdetails = await self.WOM.competitions.get_details(id=id)
        if compdetails.is_ok:
            top_10: list = []
            for i in compdetails.unwrap().participations:
                top_10.append(f'{i.participation.player.display_name} - {i.progress.gained:,}')
            top_10.sort(key=lambda x: int(x.split(' - ')[1].replace(',', '')), reverse=True)
            emoji = get(self.bot.emojis, name=f'{str(compdetails.unwrap().competition.metric).capitalize()}_icon')
            embed = discord.Embed(title=compdetails.unwrap().competition.title, color=discord.Color.blue(), description=f'**Metric**: {emoji} {str(compdetails.unwrap().competition.metric).capitalize()}\n**Time left**: <t:{int(compdetails.unwrap().competition.ends_at.timestamp())}:R>\n**Type**: {compdetails.unwrap().competition.type}', url=f"https://wiseoldman.net/competitions/{compdetails.unwrap().competition.id}")
            embed.set_footer(text=f"TOP 10 {str(compdetails.unwrap().competition.metric).capitalize()}")
            embed.add_field(
                name="Top 10",
                value='\n'.join([f'**{i.split(" - ")[0]}**: {i.split(" - ")[1]} XP' for i in top_10[:10]]),
                inline=True)
            await ctx.respond(None, embed=embed)
            return
        await ctx.respond(f'ERROR\n{compdetails.unwrap_err().message}')
        await self.WOM.close()

    @competitions.command(aliases=['newcompetition'], name='start', description='Create a new competition.')
    @commands.has_role('Staff')
    async def new_competition(self, ctx: discord.ApplicationContext): #, title: discord.Option(str, description='The title of the competition', required=True)):
        await self.WOM.start()
        modal = codeModal(title='Verification code')
        verification_code = await ctx.send_modal(modal)
        await ctx.send_followup('Please provide the verification code.')
        await self.bot.wait_for('interaction', check=lambda i: i.user == ctx.author)
        await ctx.send_followup('Let\'s create a new competition!')
        await ctx.send_followup('Please provide the title of the competition.')
        title = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        await ctx.send_followup('Please provide the metric of the competition.')
        metric = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        await ctx.send_followup('Please provide the start date of the competition.')
        start_date = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        await ctx.send_followup('Please provide the end date of the competition.')
        end_date = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
        await ctx.send_followup('Creating competition...')
        print(f'{title.content} - {metric.content} - {modal.value} - {start_date.content} - {end_date.content}')
        return
        competition = await self.WOM.competitions.create_competition(
            title=title.content,
            metric=metric.content,
            verification_code=verification_code.data,
            start_date=start_date.content,
            end_date=end_date.content
        )
        if competition.is_ok:
            await ctx.send_followup('Competition created!')
            return
        await ctx.send_followup(f'ERROR\n{competition.unwrap_err()}')
        await self.WOM.close()

    #A listener for when the cog is being unloaded
    @commands.Cog.listener()
    async def on_cog_unload(self):
        if KeyboardInterrupt:
            await self.WOM.close()
            print('WOM client closed.')
        print('Sotw cog is being unloaded.')
        self.WOM.close()

def setup(client: discord.Bot):
    client.add_cog(Competitions(client))


#For later use!
    """
    else:
            await ctx.respond(f'Getting group {id}...')
            group = await self.WOM.groups.get_gains(
                id=id,
                metric=metric,
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now()
            )
            groupdetails = await self.WOM.groups.get_details(id=id)
            if group.is_ok:
                top_10: list = []
                for i in group.unwrap():
                    top_10.append(f'{i.player.display_name} - {i.data.gained:,}')
                top_10.sort(key=lambda x: int(x.split(' - ')[1].replace(',', '')), reverse=True)
                embed = discord.Embed(title=f'{str(metric).capitalize()} Leaderboard', color=discord.Color.blue())
                embed.set_footer(text=f"{groupdetails.unwrap().group.name} - TOP 10 {str(metric).capitalize()}")
                embed.add_field(name="Name", value='\n'.join([i.split(' - ')[0] for i in top_10[:10]]), inline=True)
                embed.add_field(name="XP gained", value='\n'.join([i.split(' - ')[1] for i in top_10[:10]]), inline=True)
                await ctx.respond(None, embed=embed)
                return
            await ctx.respond(f'ERROR\n{group.unwrap_err()}')
            return
    """