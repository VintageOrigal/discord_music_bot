import discord
from discord.ext import commands, tasks
from itertools import cycle
import os
from flask import Flask, render_template
import asyncio
import json

intents = discord.Intents.all()

app = Flask(__name__)
client = commands.Bot(command_prefix='!', intents=intents)
client.remove_command("help")

# Bot Status, cycle 30sec (default)
bot_status = cycle(["Status cycle 1", "Status cycle 2", "Status Cycle 3"])
@tasks.loop(seconds=30)
async def change_status():
    await client.change_presence(activity=discord.Game(next(bot_status)))

# Discord bot commands
@client.event
async def on_ready():
    await client.tree.sync()
    print("Bot is online") # <--Can change to your bot name
    change_status.start()

async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")

@client.event
async def on_guild_join(guild):
    with open ("cogs/json/autorol.json", "r") as f:
        auto_role = json.load(f)

        auto_role[str(guild.id)] = None

        with open("cogs/json/autorole.json", "w") as f:
            json.dump(auto_role, f, intent=4)

@client.event
async def on_guild_remove(guild):
    with open("cogs/json/autorole.json", "r") as f:
        auto_role = json.load(f)

        auto_role.pop(str(guild.id))

        with open("cogs/json/autorole.json", "w") as f:
            json.dump(auto_role, f, intent=4)

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


async def main():
    async with client:
        await load()
        await client.start("MTExMDUxMDM0NDU5OTc4NTUzNA.GDea_H.Z1wKDzPjBZZ_0ram_XhkFduTbcOcPBo0Ph2_FU")

asyncio.run(main())