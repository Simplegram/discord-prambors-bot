import discord
import nextcord
import wavelink
import asyncio
import requests
import spotipy
import os
import random

from nextcord import Interaction
from nextcord.ext import commands, tasks
from random import choice
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyClientCredentials

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

intents = nextcord.Intents.default()
intents.members = True
intents.message_content = True

# IMPORTANT:
# 1. Input your bot token on line 26
# 2. Setup your SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET from Spotify Developers website
#    within your Pycharm environment variables configuration

# Input your Wavelink node detail on line 47 if you want YouTube search playback

# Input your bot token here
TOKEN = ''

bot = commands.Bot(command_prefix='woi ', intents=intents)
link = 'https://22253.live.streamtheworld.com/PRAMBORS_FM.mp3?dist=pramborsweb&tdsdk=js-2.9&pname=tdwidgets&pversion=2.9&banners=300x250&sbmid'

msg = {}

@bot.event
async def on_ready():
    print("Bot udah jalan")
    bot.loop.create_task(node_connect())

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready")

async def node_connect():
    await bot.wait_until_ready()

    # Input your wavelink node information below
    await wavelink.NodePool.create_node(bot=bot, host='localhost', port=443, password='password')

@bot.command()
async def maenin(ctx: commands.Context, *, search:wavelink.YouTubeTrack):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    embed = discord.Embed(title=f"Playing {search.title}", description=f"{search.uri}")
    embed.add_field(name="Requested by", value=ctx.author, inline=False)
    embed.add_field(name="Music Author", value=search.author, inline=True)
    embed.add_field(name="Length", value=f"{search.length} second(s)", inline=False)
    await ctx.send(embed=embed)
    await vc.play(search)

@bot.command()
async def prambors(ctx: commands.Context):
    global msg

    channel = ctx.message.author.voice.channel
    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': '-vn'}

    await ctx.message.delete()

    if not ctx.voice_client:
        await channel.connect()

    ctx.voice_client.play(discord.FFmpegPCMAudio(link, **ffmpeg_options))

    embed = discord.Embed(title='N/A')
    msg[ctx.guild.id] = await ctx.send(embed=embed)

    if getty.is_running() is False:
        getty.start()

def get_info():
    global song_title
    global song_artist
    global song_duration

    r = requests.get('https://np.tritondigital.com/public/nowplaying?mountName=PRAMBORS_FM&numberToFetch=1&eventType=track&request.preventCache=1663349779878')
    soup = BeautifulSoup(r.text, features='xml')

    track_title = soup.find('property', attrs={'name':'cue_title'})
    track_artist = soup.find('property', attrs={'name':'track_artist_name'})
    track_duration = soup.find('property', attrs={'name':'cue_time_duration'})

    song_title = track_title.contents[0].extract()
    song_artist = track_artist.contents[0].extract()
    song_duration = int(track_duration.contents[0].extract())

@tasks.loop(seconds=2)
async def getty():
    global song_duration
    global msg

    get_info()

    result = spotify.search(q=song_title)
    track = result['tracks']['items'][0]['album']['images'][0]['url']

    song_duration = song_duration/1000
    time_m = int(song_duration/60)
    time_s = int(song_duration % 60)

    embed_play = discord.Embed(title=f"PramborsFM", description=f"{song_title} - {song_artist} ({time_m}:{time_s:02})", color=0x27cce9)
    embed_play.set_footer(text="Song title won't always be accurate, kindly double check the lyrics.")
    embed_play.set_image(url=track)

    for embed in list(msg):
        await msg[embed].edit(embed=embed_play)

@bot.command()
async def tolong(ctx: commands.Context):
    embed = discord.Embed(title="Command List", description="Darkgloow command list (prefix = woi)", color=0x86c5fd)
    embed.add_field(name="prambors", value="play prambors radio", inline=True)
    embed.add_field(name="maenin {query}", value="play youtube track", inline=True)
    embed.add_field(name="diem", value="pause currently playing youtube track", inline=True)
    embed.add_field(name="resume", value="resume paused youtube track", inline=True)
    embed.add_field(name="stop", value="kill currently playing youtube track", inline=True)
    embed.add_field(name="tolong", value="summons this dialog", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def diem(ctx: commands.Context):
    vc: wavelink.Player = ctx.voice_client
    vc.pause()
    return await ctx.send("Musik di pause :grin:")

@bot.command()
async def stop(ctx: commands.Context):
    vc: wavelink.Player = ctx.voice_client
    vc.stop()
    getty.stop()
    return await ctx.send("Musik udah meninggal :skull:")

@bot.command()
async def resume(ctx: commands.Context):
    vc: wavelink.Player = ctx.voice_client
    vc.resume()
    return await ctx.send("Musik udah lanjut lagi :thumbsup:")

bot.run(TOKEN)