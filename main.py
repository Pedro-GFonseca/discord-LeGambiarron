#!/usr/bin/python3

import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from discord import Activity, ActivityType
from music_messages import login_message

load_dotenv()

activity = Activity(name="as vozes da minha cabeça", type=ActivityType.listening)
bot = commands.Bot(command_prefix='-', activity=activity,
                   intents=discord.Intents.all())

async def load():
    bot.remove_command('help')
    for filename in os.listdir("./"):
        if filename.endswith("cog.py") and not filename.startswith("main"):
            await bot.load_extension(filename[:-3])


async def main():
    async with bot:
        await load()
        await bot.start(os.getenv('DISCORD_API_TOKEN'))

@bot.event
async def on_ready():
    print(f'{bot.user}: \n', login_message)

asyncio.run(main())
