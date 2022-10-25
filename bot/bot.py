import time
from typing import List
import random
import operator
import psycopg2

import discord
from discord.ext import commands
from pytz import timezone

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='$', intents=intents)

def run(TOKEN):
    bot.run(TOKEN)

from bot.database import *

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

@bot.command(name='hello', help='Answers with an appropriate hello message')
async def hello(ctx):
    options = [
        f'Hello, {ctx.message.author.mention}!',
        f"What's up, {ctx.message.author.mention}?",
        f'Good day to you, {ctx.message.author.mention}!',
        f'Lali-ho, {ctx.message.author.mention}!',
    ]
    response = random.choice(options)
    await ctx.send(response)


@bot.command(name='init', help="Initialises the database if it isn't already."
                               "Can only be executed by admins.")
@commands.has_permissions(administrator=True)
async def init(ctx):
    success = initialize_db_with_tables()
    if success:
        await ctx.send(f"Database initialised!")
    else:
        await ctx.send('Initialisation failed in some way.')
