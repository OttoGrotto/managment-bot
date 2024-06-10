import asyncio
import re
import time
from typing import Union

import discord
import lavalink
import spotipy
from discord import slash_command, Option
from discord.ext import commands
from spotipy import SpotifyClientCredentials

RURL = re.compile(r'https?://(?:www\.)?.+')
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="38aa83e7586942c9a4fd0e0623d67326", client_secret="31b195cc830a47ab90514bc8594407dd"))


def create_embed(guild, track, position, color):
    if not track:
        return None
    try:
        url = track.extra['url']  # only present on spotify songs so people dont think im actually using youtube, hehe
    except KeyError:  # but now you know my secrets
        url = track.uri
    pos = time.strftime('%H:%M:%S', time.gmtime(int(position / 1000)))
    dur = time.strftime('%H:%M:%S', time.gmtime(int(track.duration / 1000)))
    requester = guild.get_member(track.requester).display_name
    embed = discord.Embed(title=f"{track.title}", url=url, description=f"*{track.author}*", color=color)
    embed.add_field(name="__Position__", value=f"{pos}/{dur}", inline=True)
    embed.set_footer(text=f"Requested by {requester}")
    return embed


async def cleanup(player):
    player.queue.clear()
    await player.stop()


class LavaClient(discord.VoiceClient):

    def __init__(self, client: discord.Client, channel: Union[discord.VoiceChannel, discord.StageChannel]):
        super().__init__(client, channel)
        self.client = client
        self.channel = channel
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        lavalink_data = {'t': 'VOICE_SERVER_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def on_voice_state_update(self, data):
        lavalink_data = {'t': 'VOICE_STATE_UPDATE', 'd': data}
        await self.lavalink.voice_update_handler(lavalink_data)

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False,
                      self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        self.cleanup()


class CustomPlayer(lavalink.DefaultPlayer):  # default player but with vote skipping
    def __init__(self, guild_id, node):
        super().__init__(guild_id, node)
        self.votes = []


class SongSelect(discord.ui.Select):
    def __init__(self, client, tracks, requester):
        self.client = client
        self.tracks = tracks
        self.requester = requester
        self.keys = {}

        options = []
        for track in self.tracks:
            options.append(discord.SelectOption(label=f"{track.title}", description=f"By {track.author}"))
            self.keys[f'{track.title}'] = track
        super().__init__(placeholder="Pick a song!", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.requester:
            return await interaction.response.send_message(f"Invalid user!", ephemeral=True)
        selection = self.values[0]
        song = self.keys[f"{selection}"]
        info = song['info']
        await interaction.response.edit_message(content=f"Adding {info['title']} to the player",
                                                view=None)
        player = self.client.lavalink.player_manager.get(interaction.guild.id)
        player.add(track=song, requester=self.requester.id)
        self.view.stop()
        if not player.is_playing:
            await player.play()


class Queue(discord.ui.View):

    def __init__(self, client, queue, length, color):
        super().__init__()
        self.client = client
        self.queue = queue
        self.length = length
        self.color = color
        self.position = 0
        self.max = len(queue[::10]) - 1

    def build_queue(self):
        page = 10 * self.position
        songlist = []
        count = 1
        for song in self.queue[page:page + 10]:
            songlist.append(f"**{count + page}:** `{song}`")
            count += 1
        embed = discord.Embed(title="Upcoming Songs", description=f"\n".join(songlist), color=self.color)
        embed.set_footer(text=f"{(10 * self.position - 1) + count} of {len(self.queue)} songs - {self.length}")
        return embed

    @discord.ui.button(label="Previous 10", style=discord.ButtonStyle.gray)
    async def queue_prev(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.position -= 1
        if self.position == 0:
            button.disabled = True
        if self.children[2].disabled:
            self.children[2].disabled = False
        embed = self.build_queue()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Go Back", style=discord.ButtonStyle.red)
    async def queue_return(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.client.lavalink.player_manager.get(interaction.guild.id)
        try:
            embed = create_embed(guild=interaction.guild, track=player.current, position=player.position,
                                 color=self.color)
        except AttributeError:
            return
        bview = Buttons.get_buttons(self=Buttons(self.client, self.color), player=player, user=interaction.user)
        await interaction.response.edit_message(embed=embed, view=bview)

    @discord.ui.button(label="Next 10", style=discord.ButtonStyle.gray)
    async def queue_next(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.position += 1
        if self.position == self.max:
            button.disabled = True
        if self.children[0].disabled:
            self.children[0].disabled = False
        embed = self.build_queue()
        await interaction.response.edit_message(embed=embed, view=self)


class Buttons(discord.ui.View):

    def __init__(self, client, color):
        super().__init__()
        self.client = client
        self.color = color

    def controller(self, interaction):
        player = self.client.lavalink.player_manager.get(interaction.guild.id)
        return player

    def get_buttons(self, player, user):
        if player.paused:
            self.children[0].emoji = "▶"
        if user.id in player.votes:
            self.children[1].disabled = True
        if player.shuffle:
            self.children[2].style = discord.ButtonStyle.green
        if player.loop != 0:
            emojikeys = {1: "🔂", 2: "🔁"}
            self.children[3].style = discord.ButtonStyle.green
            self.children[3].emoji = emojikeys[player.loop]
        if not self.is_privileged(user, player.current):
            buttons = [self.children[1], self.children[5]]
            self.clear_items()
            for button in buttons:
                self.add_item(button)
            if user.id in player.votes:
                self.children[0].disabled = True
        return self

    @staticmethod
    def compilequeue(queue):
        titles = []
        lengths = []
        for song in queue:
            titles.append(song.title)
            lengths.append(int(song.duration / 1000))
        return titles, lengths

    @staticmethod
    def is_privileged(user, track):
        if track:
            return track.requester == user.id or user.guild_permissions.administrator or user.is_owner()

    @discord.ui.button(emoji="⏸", style=discord.ButtonStyle.gray)
    async def button_pauseplay(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        if not self.is_privileged(interaction.user, player.current):
            return await interaction.response.send_message(f"You must be the song requester, or have kick "
                                                           f"permissions to control the player!", ephemeral=True)
        embed = create_embed(guild=interaction.guild, track=player.current, position=player.position, color=self.color)
        if not player.paused:
            button.emoji = "▶"
            await player.set_pause(pause=True)
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.channel.send(f"{interaction.user.display_name} paused the music")
        else:
            button.emoji = "⏸"
            await player.set_pause(pause=False)
            await interaction.response.edit_message(embed=embed, view=self)
            await interaction.channel.send(f"{interaction.user.display_name} resumed the music")

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.gray)
    async def button_forward(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        if interaction.user.id not in player.votes:
            player.votes.append(interaction.user.id)
        if self.is_privileged(interaction.user, player.current):
            player.votes.clear()
            await player.skip()
            await interaction.channel.send(f"{interaction.user.display_name} skipped the song")
        else:
            guild_id = player.guild_id
            guild = self.client.get_guild(guild_id)
            voice_members = []
            votes = len(player.votes)
            for user in guild.voice_client.channel.members:
                if not user.bot:
                    voice_members.append(user.id)
            users = len(voice_members)
            required = round(users / 1)
            if votes >= required:
                player.votes.clear()
                await player.skip()
                await interaction.channel.send(f"{interaction.user.display_name} voted and the song was skipped!")
            else:
                button.disabled = True
                await interaction.channel.send(f"{interaction.user.display_name} voted to skip! ({votes}/{required})")
        if player.is_playing:
            embed = create_embed(guild=interaction.guild, track=player.current, position=player.position,
                                 color=self.color)
            view = self
        else:
            embed = discord.Embed(title=f"Empty queue, stopping player...", color=discord.Color.red())
            view = None
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.gray)
    async def button_shuffle(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        if not self.is_privileged(interaction.user, player.current):
            return await interaction.response.send_message(f"You must be the song requester, or have kick "
                                                           f"permissions to control the player!", ephemeral=True)
        embed = create_embed(guild=interaction.guild, track=player.current, position=player.position, color=self.color)
        if not player.shuffle:
            player.set_shuffle(shuffle=True)
            button.style = discord.ButtonStyle.green
            await interaction.channel.send(f"{interaction.user.display_name} shuffling the queue!")
        else:
            player.set_shuffle(shuffle=False)
            button.style = discord.ButtonStyle.gray
            await interaction.channel.send(f"{interaction.user.display_name} no longer shuffling the queue!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.gray)
    async def button_loop(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        if not self.is_privileged(interaction.user, player.current):
            return await interaction.response.send_message(f"You must be the song requester, or have kick "
                                                           f"permissions to control the player!", ephemeral=True)
        embed = create_embed(guild=interaction.guild, track=player.current, position=player.position, color=self.color)
        match player.loop:
            case player.LOOP_NONE:
                player.set_loop(1)
                button.emoji = "🔂"
                button.style = discord.ButtonStyle.green
                await interaction.channel.send(f"{interaction.user.display_name} is looping the song!")
            case player.LOOP_SINGLE:
                player.set_loop(2)
                button.emoji = "🔁"
                await interaction.channel.send(f"{interaction.user.display_name} is looping the queue!")
            case player.LOOP_QUEUE:
                player.set_loop(0)
                button.style = discord.ButtonStyle.gray
                await interaction.channel.send(f"{interaction.user.display_name} disabled the loop!")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="⏹", style=discord.ButtonStyle.red)
    async def button_stop(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        if not self.is_privileged(interaction.user, player.current):
            return await interaction.response.send_message(f"You must be the song requester, or have kick "
                                                           f"permissions to control the player!", ephemeral=True)
        embed = discord.Embed(title=f"Stopping player...", color=discord.Color.red())
        voice = interaction.guild.voice_client
        await interaction.response.edit_message(embed=embed, view=None)
        await interaction.channel.send(f"{interaction.user.display_name} stopped the player")
        if voice:
            await voice.disconnect(force=True)
        await cleanup(player)

    @discord.ui.button(emoji="⏏️", label="Queue", style=discord.ButtonStyle.blurple)
    async def button_queue(self, button: discord.ui.Button, interaction: discord.Interaction):
        player = self.controller(interaction)
        queue, length = self.compilequeue(player.queue)
        songlist = []
        for index, song in enumerate(queue[:10]):
            songlist.append(f"**{index + 1}:** `{song}`")
        totallength = time.strftime('%H hours, %M minutes, %S seconds', time.gmtime(sum(length)))
        embed = discord.Embed(title="Upcoming Songs", description=f"\n".join(songlist), color=self.color)
        embed.set_footer(text=f"10 of {len(queue)} songs - {totallength}")
        view = Queue(self.client, queue, totallength, self.color)
        #ex = view.children[1:] if len(queue) > 10 else view.children[1:2]
        #view.disable_all_items(exclusions=ex)
        await interaction.response.edit_message(embed=embed, view=view)


class Music(commands.Cog):

    def __init__(self, client):
        print('Music cog is ready.')
        self.client: discord.Bot = client
        self.client.lavalink = None
        client.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.client.wait_until_ready()
        lavaclient = lavalink.Client(user_id=self.client.user.id, player=CustomPlayer)
        lavaclient.add_node(host='lavalink.teramont.net', port=25565, password='eHKuFcz67k4lBS64', ssl=False)
        lavaclient.add_event_hooks(self)
        self.client.lavalink = lavaclient

    @lavalink.listener(lavalink.events.QueueEndEvent)
    async def event_queue_end(self, event: lavalink.QueueEndEvent):
        guild_id = event.player.guild_id
        guild = self.client.get_guild(guild_id)
        #await guild.voice_client.disconnect(force=True)
        self.get_spotify_tracks("https://www.youtube.com/watch?v=SlPhMPnQ58k&list=RDSlPhMPnQ58k&start_radio=1&rv=SlPhMPnQ58k&t=1")

    @lavalink.listener(lavalink.events.TrackEndEvent)
    async def event_track_end(self, event: lavalink.TrackEndEvent):
        event.player.votes.clear()

    @staticmethod
    def get_spotify_tracks(query):  # spotify you suck this took so long to figure out
        songlist = []
        urllist = []
        attempt = re.findall(r'/track/|/album/|/playlist/', query)
        if not attempt:
            return None
        match attempt[0]:
            case '/track/':
                track = sp.track(query)
                songlist.append(f"{track['album']['artists'][0]['name']} - {track['name']}")
                urllist.append(track['external_urls']['spotify'])
            case '/album/':
                tracks = sp.album(query)
                for track in tracks['tracks']['items']:
                    songlist.append(f"{track['artists'][0]['name']} - {track['name']}")
                    urllist.append(track['external_urls']['spotify'])
            case '/playlist/':
                tracks = sp.playlist(query)
                for track in tracks['tracks']['items']:
                    actualtrack = track['track']  # why
                    songlist.append(f"{actualtrack['album']['artists'][0]['name']} - {actualtrack['name']}")
                    urllist.append(actualtrack['external_urls']['spotify'])
            case _:
                pass
        return songlist, urllist

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState,
                                    after: discord.VoiceState):
        voice = discord.utils.get(self.client.voice_clients, guild=member.guild)
        player = self.client.lavalink.player_manager.get(member.guild.id)
        if not voice:
            if player:
                await cleanup(player)
            return
        elif voice.channel != before.channel:  # ignore if the member joined a voice channel
            return
        elif member.bot:
            return
        if after.channel != before.channel:
            memberlist = []
            for m in before.channel.members:
                if not m.bot:
                    memberlist.append(m.id)
            if player.current and player.current.requester not in memberlist:
                player.votes.clear()
            if not memberlist:
                if player.is_playing:
                    await cleanup(player)
                await voice.disconnect(force=True)

    @slash_command(name = "music", description="Play some music")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def music(self, ctx, search: Option(str, description="Music query or URL", required=False, default=None)):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.respond(f"You need to be in a voice channel", ephemeral=True)
        player = self.client.lavalink.player_manager.create(ctx.guild.id)
        try:
            await channel.connect(cls=LavaClient)
        except discord.ClientException:
            await ctx.guild.voice_client.move_to(channel)
        if search:
            if len(search) > 256:
                return await ctx.respond(f"Search query has a maximum of 256 characters!", ephemeral=True)
            elif player.is_playing:
                if len(player.queue) >= 250:
                    return await ctx.respond(f"The queue is full!", ephemeral=True)
            search = f'ytsearch:{search}' if not RURL.match(search) else search
            try:
                results = await player.node.get_tracks(search)
            except lavalink.errors.NodeError:
                return await ctx.respond(f"Couldn't find any music!", ephemeral=True)
            tracks = results.tracks
            total = len(player.queue)
            match results.load_type:
                case lavalink.LoadType.PLAYLIST:
                    await ctx.defer()
                    count = 0
                    for track in tracks:
                        if total + count < 250:
                            player.add(track=track, requester=ctx.author.id)
                            count += 1
                    await ctx.respond(f"Added {count} songs to the player")
                    if not player.is_playing:
                        await player.play()
                case lavalink.LoadType.TRACK:
                    song = tracks[0]
                    await ctx.respond(f"Adding {song.title} to the player")
                    player.add(track=song, requester=ctx.author.id)
                    if not player.is_playing:
                        await player.play()
                case lavalink.LoadType.SEARCH:
                    view = discord.ui.View(timeout=30)
                    view.add_item(SongSelect(self.client, tracks[:5], ctx.author))
                    message = await ctx.respond(view=view)
                    test_for_response = await view.wait()
                    if test_for_response:  # returns True if a song wasn't picked
                        embed = discord.Embed(
                            title=f"No song selected! Cancelling...", color=discord.Color.red())
                        await message.edit_original_message(embed=embed, view=None)
                case _:
                    if 'open.spotify.com' in search:
                        spotifysongs, spotifyurls = self.get_spotify_tracks(query=search)
                        if not spotifysongs:
                            return await ctx.respond(f"Couldn't find any music!", ephemeral=True)
                        await ctx.defer()
                        s_results = await asyncio.wait_for(asyncio.gather(*[player.node.get_tracks(
                            f'ytsearch:{song}') for song in spotifysongs]), timeout=30)
                        count = 0
                        for track, url in zip(s_results, spotifyurls):
                            if total + count < 250:
                                the_track = track.tracks[0]
                                the_track.extra['url'] = url
                                player.add(track=the_track, requester=ctx.author.id)
                                count += 1
                        await ctx.respond(f"Added {count} spotify song(s) to the player")
                        if not player.is_playing:
                            await player.play()
                    else:
                        return await ctx.respond(f"Couldn't find any music!", ephemeral=True)
        else:
            if not player.is_playing:
                return await ctx.respond(f"No music playing!", ephemeral=True)
            color = ctx.guild.me.color
            bview = Buttons.get_buttons(self=Buttons(self.client, color), player=player, user=ctx.author)
            embed = create_embed(guild=ctx.guild, track=player.current, position=player.position, color=color)
            await ctx.respond(embed=embed, view=bview, ephemeral=True)


def setup(client):
    client.add_cog(Music(client))