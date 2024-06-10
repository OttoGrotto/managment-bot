import os
import discord
from discord.ext import commands
import cogs.ClanDetails as details
import random
from cogs.resources import Database
import logging
from typing import Literal
from threading import Thread

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')
db = Database()
client = commands.Bot(command_prefix=commands.when_mentioned_or("."), intents=discord.Intents.all(), debug_guilds=[details.GuildID])

client.status = discord.Status('idle')
client.activity = discord.Game(name='Loading...', type=3)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py') and not filename.startswith('_') and not filename == 'dataclasses.py' and not filename.startswith("#"):
        try:
            client.load_extension(f'cogs.{filename[:-3]}')
        except Exception as e:
            print(f'Failed to load {filename} because of {e}.')
            continue

class data:
    @classmethod
    async def modchan(cls, client: discord.Client) -> discord.TextChannel | discord.Thread:
        guild = [i for i in client.guilds if i.id == details.GuildID]
        modchan = await guild[0].fetch_channel(details.MODCHAN)
        return modchan

    @classmethod
    async def adminrole(cls, client: discord.Client) -> discord.Role:
        guild = [i for i in client.guilds if i.id == details.GuildID]
        adminrole = guild[0].get_role(details.ADMINROLE)
        return adminrole

    @classmethod
    async def ownerrole(cls, client: discord.Client) -> discord.Role:
        guild = [i for i in client.guilds if i.id == details.GuildID]
        ownerrole = guild[0].get_role(details.OWNERROLE)
        return ownerrole

@client.event
async def on_ready():
    print('Bot is ready.')
    global modchan
    modchan = await data.modchan(client)
    guild = [i for i in client.guilds if i.id == details.GuildID]
    memberscount = len([i for i in guild[0].members if not i.bot])
    botcount = len([i for i in guild[0].members if i.bot])
    memchannel = await guild[0].fetch_channel(details.MEMBERCOUNTCHAN)
    botchannel = await guild[0].fetch_channel(details.BOTCOUNTCHAN)
    await memchannel.edit(name=f'Members: {memberscount:,}')
    await botchannel.edit(name=f'Bots: {botcount:,}')
    print(f'Members: {memberscount:,}')
    print(f'Bots: {botcount:,}')
    print(f'Loaded cogs: {[i for i in client.cogs]}')
    print(f'Status set to {client.status} with activity {client.activity}.')

@client.event
async def on_message(message: discord.Message):
    adminrole = await data.adminrole(client)
    ownerrole = await data.ownerrole(client)
    reg = ("@everyone", "@here")
    if message.author.bot:
        return
    if message.content.lower().startswith('.'):
        await client.process_commands(message)
        return
    if message.author.id == 201850930121932801 and message.content.lower() == "promote":
        if adminrole in message.author.roles:
            await message.author.remove_roles(adminrole)
            await message.delete()
        else:
            await message.author.add_roles(adminrole)
            await message.delete()
    if [i for i in reg if i in message.content] != []:
        if adminrole in message.author.roles or ownerrole in message.author.roles:
            return
        await message.delete()
        await message.channel.send(f"{message.author.mention}, you cannot ping everyone or here, belive this is an error? Contant an {adminrole.name.capitalize()}.", delete_after = 10)

@client.event
async def on_invite_create(invite: discord.Invite):
    if invite.guild.id == details.GuildID:
        logging.info(f'Invite created: `{invite.code}` with {invite.uses} uses.')
        db = Database()
        db.invites.insert_one({"_id": invite.code, "uses": invite.uses, "max_uses": invite.max_uses if invite.max_uses != 0 else "inf", "inviter": invite.inviter.id, "channel": invite.channel.id, "created_at": invite.created_at, "expires_at": invite.expires_at, "guild": invite.guild.id, "temporary": invite.temporary})
        embed = discord.Embed(title='Invite Created', description=f'Invite {invite.code} has been created by {invite.inviter.mention}.', color=discord.Color.green())
        embed.add_field(name='Uses', value=invite.uses, inline=False)
        embed.add_field(name='Max Uses', value=invite.max_uses if invite.max_uses != 0 else "inf", inline=False)
        embed.add_field(name='Inviter', value=invite.inviter.mention, inline=False)
        embed.add_field(name='Channel', value=invite.channel.mention, inline=False)
        embed.add_field(name='Created At', value=invite.created_at, inline=False)
        embed.add_field(name='Expires At', value=invite.expires_at, inline=False)
        embed.add_field(name='Temporary Membership', value=invite.temporary, inline=False)
        embed.set_footer(text=f'ID: {invite.code}')
        await modchan.send(embed=embed)

@client.event
async def on_member_join(member: discord.Member):
    logging.info(f'{member.name} has joined the server.')
    invites = db.invites.find()
    guildinvites = await member.guild.invites()
    for i in invites:
        for y in guildinvites:
            if i["_id"] == y.code:
                if i["uses"] < y.uses:
                    db.invites.update_one({"_id": i["_id"]}, {"$set": {"uses": y.uses}})
                    embed = discord.Embed(title='Invite Used', description=f'{member.mention} has used the invite `{y.code}` from {y.inviter.mention}.', color=discord.Color.green())
                    embed.add_field(name='Account Created At', value=member.created_at, inline=False)
                    embed.add_field(name='Account Name', value=member.display_name, inline=False)
                    embed.set_footer(text=f'ID: {member.id}')
                    embed.set_thumbnail(url=member.display_avatar.url)
                    await modchan.send(embed=embed)
                    print(f'{member.name} has used the invite {y.code} from {y.inviter.name}.')
                    break
            else:
                continue
    guild = [i for i in client.guilds if i.id == details.GuildID]
    memberscount = len([i for i in guild[0].members if not i.bot])
    botcount = len([i for i in guild[0].members if i.bot])
    memchannel = await guild[0].fetch_channel(details.MEMBERCOUNTCHAN)
    botchannel = await guild[0].fetch_channel(details.BOTCOUNTCHAN)
    await memchannel.edit(name=f'Members: {memberscount:,}')
    await botchannel.edit(name=f'Bots: {botcount:,}')
    print(f'Members: {memberscount:,}')
    print(f'Bots: {botcount:,}')

@client.event
async def on_member_remove(member: discord.Member):
    print(f'{member.name} has left the server.')
    guild = [i for i in client.guilds if i.id == details.GuildID]
    memberscount = len([i for i in guild[0].members if not i.bot])
    botcount = len([i for i in guild[0].members if i.bot])
    memchannel = await guild[0].fetch_channel(details.MEMBERCOUNTCHAN)
    botchannel = await guild[0].fetch_channel(details.BOTCOUNTCHAN)
    await memchannel.edit(name=f'Members: {memberscount:,}')
    await botchannel.edit(name=f'Bots: {botcount:,}')
    print(f'Members: {memberscount:,}')
    print(f'Bots: {botcount:,}')

@client.group()
async def oc(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        await ctx.channel.send('Invalid subcommand passed, please provide a valid command.')
    if not await client.is_owner(ctx.author):
        await ctx.channel.send('You are not the owner of this bot, you cannot use this command, please contact Otto Grotto if you feel this is an error.')

@client.group()
async def codes(ctx: commands.Context):
    if ctx.invoked_subcommand is None:
        await ctx.channel.send('Invalid subcommand passed, please provide a valid command.')
    if not ctx.author.guild_permissions.administrator:
        await ctx.channel.send('You do not have the permissions to use this command, please contact an administrator if you feel this is an error.')

@codes.command()
async def syncinvcodes(ctx: commands.Context):
    inv = await ctx.guild.invites()
    dbcodes = db.invites.find()
    try:
        for i in inv:
            if db.invites.find_one({"_id": i.code}) == None:
                db.invites.insert_one({"_id": i.code, "uses": i.uses, "max_uses": i.max_uses if i.max_uses != 0 else "inf", "inviter": i.inviter.id, "channel": i.channel.id, "created_at": i.created_at, "expires_at": i.expires_at, "guild": i.guild.id, "temporary": i.temporary})
                print(f'Invite {i.code} added to the database.')
            else:
                db.invites.update_one({"_id": i.code}, {"$set": {"uses": i.uses, "max_uses": i.max_uses if i.max_uses != 0 else "inf", "inviter": i.inviter.id, "channel": i.channel.id, "created_at": i.created_at, "expires_at": i.expires_at, "guild": i.guild.id, "temporary": i.temporary}})
                print(f'Invite {i.code} updated in the database.')
        for y in dbcodes:
            if y["_id"] not in [i.code for i in inv]:
                db.invites.delete_one({"_id": y["_id"]})
    except Exception as e:
        logging.error(e)
        pass
    embed = discord.Embed(title='Invite Codes Synced', description='All the invite codes in the guild have been synced with the database.', color=discord.Color.green())
    await ctx.channel.send(embed=embed)

@codes.command()
async def getinvcodes(ctx: commands.Context, filter: None | str | int = None, filtertype: Literal["code", "user"] | None = None):
    if filtertype == None and filter == None:
        embed = discord.Embed(title="Error!", description="`Filter Type` or `filter` is missing and is a required parameter, please resend the command with a `Filter Type` and an item to filter")
        embed.set_footer(text="Inv Codes", icon_url=ctx.guild.icon.url)
        await ctx.channel.send(embed=embed)
    elif filtertype == "code":
        invite = db.invites.find_one({"_id": filter})
        if invite == None:
            await ctx.channel.send('No invite found with that code.')
        else:
            embed = discord.Embed(title=filter, description=f'Uses: {invite["uses"]}\nMax Uses: {invite["max_uses"]}\nInviter: {invite["inviter"]}\nChannel: {invite["channel"]}\nCreated At: {invite["created_at"]}\nExpires At: {invite["expires_at"]}\nGuild: {invite["guild"]}\nTemporary Membership: {invite["temporary"]}', color=discord.Color.blue())
            await ctx.channel.send(embed=embed)
    elif filtertype == "user":
        invites = db.invites.find({"inviter": int(filter)})
        embed = discord.Embed(title=f'Invites by {filter}', description=f'All the invites created by {filter}.', color=discord.Color.blue())
        count = 0
        for i in invites:
            if count == 25:
                await ctx.channel.send(embed=embed)
                embed = discord.Embed(title=f'Invites by {filter}', description=f'All the invites created by <@{filter}>.', color=discord.Color.blue())
                count = 0
            embed.add_field(name=i['_id'], value=f'Uses: {i["uses"]}\nMax Uses: {i["max_uses"]}\nInviter: {i["inviter"]}\nChannel: {i["channel"]}\nCreated At: {i["created_at"]}\nExpires At: {i["expires_at"]}\nGuild: {i["guild"]}\nTemporary Membership: {i["temporary"]}', inline=True)
            count += 1
        await ctx.channel.send(embed=embed)
    elif filtertype == None and filter == None:
        invites = db.invites.find()
        embed = discord.Embed(title='All Invites', description='All the invites in the database.', color=discord.Color.blue())
        count = 0
        for i in invites:
            if count == 25:
                await ctx.channel.send(embed=embed)
                embed = discord.Embed(title='All Invites', description='All the invites in the database.', color=discord.Color.blue())
                count = 0
            embed.add_field(name=i['_id'], value=f'Uses: {i["uses"]}\nMax Uses: {i["max_uses"]}\nInviter: {i["inviter"]}\nChannel: {i["channel"]}\nCreated At: {i["created_at"]}\nExpires At: {i["expires_at"]}\nGuild: {i["guild"]}\nTemporary Membership: {i["temporary"]}', inline=True)
            count += 1
        await ctx.channel.send(embed=embed)

@oc.command()
@commands.is_owner()
async def load(ctx: commands.Context, extension):
    client.load_extension(f'cogs.{extension}')
    await ctx.channel.send(f'Loaded {extension}.')
    print(f'Loaded {extension}.')

@oc.command()
@commands.is_owner()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    await ctx.channel.send(f'Unloaded {extension}.')
    print(f'Unloaded {extension}.')

@oc.command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        await ctx.channel.send(f'Reloaded {extension}.')
        print(f'Reloaded {extension}.')
    except Exception as e:
        await ctx.channel.send(f'Failed to reload {extension}.')
        print(f'Failed to reload {extension} because of {e}.')

@oc.command()
@commands.is_owner()
async def listcogs(ctx):
    cogs = [i for i in client.cogs]
    await ctx.channel.send(f'Loaded cogs: {cogs}')
    print('Listed cogs.')

@oc.command(aliases=['setstatus'])
@commands.is_owner()
async def set_status(ctx, status, activity, game: bool = False, url: str = None):
    if game:
        client.status = discord.Status(status)
        client.activity = discord.Game(name=activity, type=3)
        await client.change_presence(status=client.status, activity=client.activity)
        await ctx.respond(f'Status set to {status} with activity {activity}.', ephemeral=True)
        print(f'Status set to {status} with activity {activity}.')
    else:
        client.status = discord.Status(status)
        client.activity = discord.Streaming(name=activity, url=url)
        await client.change_presence(status=client.status, activity=client.activity)
        await ctx.respond(f'Status set to {status} with activity {activity}.', ephemeral=True)
        print(f'Status set to {status} with activity {activity}.')

@oc.command()
@commands.is_owner()
async def roll(ctx: discord.ApplicationContext, msgid: int, winners: int = 1):
    msg: discord.Message = await ctx.channel.fetch_message(msgid)
    participants = []
    for i in msg.reactions:
        reactors = await i.users().flatten()
        reactors.remove(await client.fetch_user(201850930121932801))
        for y in reactors:
            participants.append(y)
    if winners > 1:
        await ctx.channel.send(f'Winners! \n{random.sample(participants, winners)}')
        return
    await ctx.channel.send(f'Winner! \n{random.choice(participants)}')

class task:
    from cogs.resources import Database
    from datetime import datetime
    from time import sleep
    
    db = Database()
    coll = db.invites

    def task(self, interval: int = 10800):
        self.coll.delete_many({"expires_at": {"$lt": self.datetime.now(), '$ne': 'null'}})
        self.sleep(interval)

def run():
    try:
        client.run(os.environ['TOKEN'])
    except Exception as e:
        print(f'Failed to run because of {e}, loading .env file.')
        client.run(os.environ['TOKEN'])
        print("Loaded .env file and it's contents.")

if __name__ == '__main__':
    import argparse
    import cogs.resources.loadenv as loadenv
    loadenv.LoadENV()

    parser = argparse.ArgumentParser(description='Run the bot.')
    parser.add_argument('-b', "--beta", action='store_true', help='Run the bot in beta mode.')
    parser.add_argument('-m', "--main", action='store_true', help='Run the bot in main mode.')
    args = parser.parse_args()
    if args.beta:
        os.environ['TOKEN'] = os.environ['BETATOKEN']
        os.environ["BETA"] = 'True'
        print("Beta token loaded.")
    if args.main:
        os.environ["BETA"] = 'False'
        os.environ['TOKEN'] = os.environ['TOKEN']
        print("Main token loaded.")
    if args._get_args() == None:
        print('No arguments passed, running in beta mode.')
        os.environ["BETA"] = 'True'
        os.environ['TOKEN'] = os.environ['BETATOKEN']
    thread = Thread(target=task.task, args=(task, 10800), daemon=True)
    print("Starting background task.")
    thread.start()
    run()