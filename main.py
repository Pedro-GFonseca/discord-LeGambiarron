import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
from discord import Activity, ActivityType

load_dotenv()

activity = Activity(name="!help", type=ActivityType.listening)
bot = commands.Bot(command_prefix='-', activity=activity,
                   intents=discord.Intents.all())

async def load():
    bot.remove_command('help')
    for filename in os.listdir("./discord-sounds-bot"):
        if filename.endswith("cog.py") and not filename.startswith("lgbot"):
            await bot.load_extension(filename[:-3])


async def main():
    async with bot:
        await load()
        await bot.start(os.getenv('DISCORD_API_TOKEN'))

@bot.event
async def on_ready():
    print('o pai tá on')

asyncio.run(main())