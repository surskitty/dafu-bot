import time
from typing import List
import random
import operator
import psycopg2
import re

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

@bot.command(name='healthcheck', help='Tests if the database connection is working')
async def healthcheck(ctx):
    conn = create_connection()
    if conn is not None:
        response = f'Seems good, {ctx.message.author.mention}!'
    else:
        response = f"Something isn't right."
    await ctx.send(response)
    conn.close()

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

def make_raider_embed(raider):
    embed = discord.Embed(title=raider.name, description=raider.roles,
                          color=discord.Color.dark_gold())
    embed.add_field(name="**Preferred role**", value=ROLES_FULL[raider.preferred_role], inline=False)
    embed.add_field(name="**Volunteer for Party Lead**", value=str(raider.party_lead), inline=False)
    embed.add_field(name="**Set to Reserve Only**", value=str(raider.reserve), inline=False)
    embed.set_footer(text=f"Orb Ponderer #{raider.id}")
    return embed

@bot.command(name='init', help="Initialises the database if it isn't already."
                               "Can only be executed by admins.")
@commands.has_permissions(administrator=True)
async def init(ctx):
    success = initialize_db_with_tables()
    if success:
        await ctx.send(f"Database initialised!")
    else:
        await ctx.send('Initialisation failed in some way.')

@bot.command(name='register', help='Registers your character')
async def register(ctx, character_name: str, roles: str, preferred_role='d'):
    discord_id = int(ctx.message.author.id)
    conn = create_connection()
    if conn is not None:
        db_chara = get_raider_id_by_discord_id(conn, discord_id)
        if db_chara:
            await ctx.send(f"<@{discord_id}> is already registered!")
            return
        try:
            character_name = re.sub(r'[^A-Za-z0-9 #]+', '', character_name) 
            roles = roles.lower()
            role_list = roles.split(",")
            roles_temp = []
            for x in role_list:
                if x in ROLES:        roles_temp.add(x)
                elif x in ROLES_FULL: roles_temp.add(x[0])
            roles_temp = set(roles_temp)
            roles_temp = list(roles_temp)
            roles_temp.sort()
            roles = ""
            for x in roles_temp:
                roles += x
            if preferred_role in ROLES:        preferred_role = preferred_role
            elif preferred_role in ROLES_FULL: preferred_role = preferred_role[0]
            else:                              preferred_role = "d"
        
            create_raider(conn, discord_id, character_name, roles, preferred_role)
            conn.commit()
            raider = make_raider_from_db(conn, 0, discord_id)
            conn.close()
            embed = make_raider_embed(raider)
            await ctx.send(f"<@{raider.discord_id}>'s character:", embed=embed)
        except Exception as e:
            conn.close()
            await ctx.send('Could not parse name and/or role list. '
                           'Format like this: `$register "Firstname Lastname" "tank,caster,healer" dps`')
            return

    else:
        await ctx.send('Could not connect to database. Need connection to create and save characters.')
        return

