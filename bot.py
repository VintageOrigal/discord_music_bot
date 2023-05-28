import discord
from discord.ext import commands, tasks
from itertools import cycle
import os
from flask import Flask, render_template
import asyncio
import json
from dotenv import load_dotenv
import youtube_dl

load_dotenv()
# Get the API token from the .env file
DISCORD_TOKEN = os.getenv("discord_token")

intents = discord.Intents.all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)
app = Flask(__name__)

# Youtube audio format

youtube_dl.utils.bug_reports_message = "lambda"

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quite': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data: 
            # take first item from playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

# Bot Status, cycle 30sec (default)
bot_status = cycle(["Status cycle 1", "Status cycle 2", "Status Cycle 3"])
@tasks.loop(seconds=30)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))

# Discord bot commands
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot is online") # <--Can change to your bot name
    change_status.start()

# Sending gifs on start-up and prints server details

@bot.event
async def on_ready():
    for guild in bot.guilds:
        for channel in guild.text_channels :
            if str(channel) == "general" :
                await channel.send('Bot Active..')
                await channel.send(file=discord.File('add_gif_file_name_here.png'))
        print('Active in {}\n Menmber Count: {}'.format(guild.name,guild.member_count))

@bot.command(help="Prints details of the Server")
async def where_am_i(ctx):
    owner=str(ctx.guild.owner)
    region=str(ctx.guild.region)
    guild_id=str(ctx.guild.id)
    memberCount=str(ctx.guild.member_count)
    icon=str(ctx.guild.icon_url)
    desc=ctx.guild.description

    embed=discord.embed(
        title=ctx.guild.name + "Server Information",
        description=desc,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=guild_id, inline=True)
    embed.add_field(name="Region", value=region, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)

    await ctx.send(embed=embed)

    members=[]
    async for member in ctx.guild.fetch_members(limit=150):
        await ctx.send('Name: {}\t Status: {}\n Joined at {}'.format(members.display_name,str(members.status),str(members.joined_at)))

@bot.command()
async def tell_me_about_yourself(ctx):
    text = "My name is Bumbot!/n I was build by VintageOrigal. At present I have limited features(find out more by tping !help)/n :"
    await ctx.send(text)

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.event
async def on_guild_join(guild):
    with open ("cogs/json/autorol.json", "r") as f:
        auto_role = json.load(f)

        auto_role[str(guild.id)] = None

        with open("cogs/json/autorole.json", "w") as f:
            json.dump(auto_role, f, intent=4)

@bot.event
async def on_guild_remove(guild):
    with open("cogs/json/autorole.json", "r") as f:
        auto_role = json.load(f)

        auto_role.pop(str(guild.id))

        with open("cogs/json/autorole.json", "w") as f:
            json.dump(auto_role, f, intent=4)

# Join and Leave commands

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
        await channel.connect()

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to voice channel.")

# Play, Pause, Resume, Stop commands

# Play command

@bot.command(name='play_song', help='To Play songs')
async def play(ctx,url):
    try :
        server = ctx.message.guild
        voice_channel = server.voice_channel

        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpes.exe", source="filename"))
            await ctx.send('**Now playing:** {}'.format(filename))
    except:
        await ctx.send("The bot is not connected to a voice channel.")

#Puase command

@bot.command(name='pause', help='This command pause the song.')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

# Resume command

@bot.command(name='resume', help='Resume the song.')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

# Stop command

@bot.command(name='stop', help='Stop the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

# Flask web routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/play', methods=['POST'])
def play_song():
    # Implement the logic to handel the song request from the web interface
    pass

@app.route('/pause', methods=['POST'])
def pause_song():
    # Implement the logic to pause the currently playing song from the web interface
    pass

asyncio.run(main())