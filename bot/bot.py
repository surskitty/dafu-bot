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

@bot.command(name='healthcheck', help='Tests if the database connection is working', hidden=True)
async def healthcheck(ctx):
    conn = create_connection()
    if conn is not None:
        response = f'Seems good, {ctx.message.author.mention}!'
    else:
        response = f"Something isn't right."
    await ctx.send(response)
    conn.close()

@bot.command(name='hello', help='Answers with an appropriate hello message', hidden=True)
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
    embed = discord.Embed(title=raider.name, description=raider.role_string(),
                          color=discord.Color.dark_gold())
    embed.add_field(name="**Preferred role**", value=EXPAND_ROLES[raider.preferred_role], inline=False)
    if raider.party_lead: embed.add_field(name="**Volunteering for Party Lead**", value="Cat wrangling commence!", inline=False)
    if raider.reserve:    embed.add_field(name="**Benchwarmer**", value="Only going to runs that need bodies", inline=False)
    embed.set_footer(text=f"Orb Ponderer #{raider.id}")
    return embed

@bot.command(name='register', brief="Registers your character with the bot.",
    help="""Registers your character with the bot. 
    Format as `$register 'Meteor Survivor' tank,healer,ranged,caster dps`.
    The first list of roles is all roles you're willing to play as; the one after the space is the one you prefer. 
    Note that signing up as ranged or caster mean that you are willing to bring Lost Dervish or Lost Cure IV!""")
async def register(ctx, character_name: str, roles: str, preferred_role='dps'):
    discord_id = int(ctx.message.author.id)
    conn = create_connection()
    if conn is not None:
        db_chara = get_raider_id_by_discord_id(conn, discord_id)
        if db_chara:
            await ctx.send(f"<@{discord_id}> is already registered!")
            return
        try:
            character_name = re.sub(r"[^A-Za-z0-9 #']+", '', character_name)
            roles, preferred_role = sanitize_roles(roles, preferred_role)
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

@bot.command(name='changename', help="Changes your listed character name")
async def changename(ctx, character_name):
    discord_id = int(ctx.message.author.id)
    conn = create_connection()
    if conn is not None:
        raider_id = get_raider_id_by_discord_id(conn, discord_id)
        if not raider_id:
            await ctx.send(f"<@{discord_id}> is not currently registered. `$register` first.")
            return
        raider = make_raider_from_db(conn, 0, discord_id)
        character_name = re.sub(r"[^A-Za-z0-9 #']+", '', character_name)
        update_raider(conn, "character_name", character_name, raider.id)
        conn.commit()
        raider = make_raider_from_db(conn, 0, discord_id)
        embed = make_raider_embed(raider)
        await ctx.send(f"<@{discord_id}>'s character:", embed=embed)
        conn.close()
    else:
        await ctx.send('Could not connect to database!')
        return

@bot.command(name='whoami', brief="Checks whether you're registered in the database, and how.")
async def whoami(ctx):
    discord_id = int(ctx.message.author.id)
    conn = create_connection()
    if conn is not None:
        raider_id = get_raider_id_by_discord_id(conn, discord_id)
        if not raider_id:
            await ctx.send(f"<@{discord_id}> is not currently registered. `$register` first.")
            return
        raider = make_raider_from_db(conn, 0, discord_id)
        embed = make_raider_embed(raider)
        await ctx.send(f"<@{discord_id}>'s character:", embed=embed)
        conn.close()
    else:
        await ctx.send('Could not connect to database!')
        return

@bot.command(name='partylead', help="Toggles whether or not you're volunteering for party leading.")
async def partylead(ctx):
    discord_id = int(ctx.message.author.id)
    conn = create_connection()
    if conn is not None:
        raider_id = get_raider_id_by_discord_id(conn, discord_id)
        if not raider_id:
            await ctx.send(f"<@{discord_id}> is not currently registered. `$register` first.")
            return
        raider = make_raider_from_db(conn, 0, discord_id)
        if raider.party_lead:
            raider.party_lead = False
            update_raider(conn, "party_lead", False, raider.id)
            await ctx.send('<@{discord_id}> is no longer volunteering to party lead.')
        else:
            raider.party_lead = True
            update_raider(conn, "party_lead", True, raider.id)
            await ctx.send("<@{discord_id}> may get asked to party lead! This consists primary of placing markers and communicating between your party and the raid host, _not_ necessarily calling.")
        conn.commit()
        conn.close()
    else:
        await ctx.send('Could not connect to database!')
        return

@bot.command(name='setroles', help="Sets your roles in the database")
async def setroles(ctx, roles: str, preferred_role='d'):
    discord_id = int(ctx.message.author.id)
    conn = create_connection()
    if conn is not None:
        raider_id = get_raider_id_by_discord_id(conn, discord_id)
        if not raider_id:
            await ctx.send(f"<@{discord_id}> is not currently registered. `$register` first.")
            return
        raider = make_raider_from_db(conn, 0, discord_id)
        set_preferred = False
        if preferred_role is not None or preferred_role != "":
            set_preferred = True
        roles, preferred_role = sanitize_roles(roles, preferred_role)
        update_raider(conn, "roles", roles, raider.id)
        if set_preferred: update_raider(conn, "preferred_role", preferred_role, raider.id)
        conn.commit()
        raider = make_raider_from_db(conn, 0, discord_id)
        embed = make_raider_embed(raider)
        await ctx.send(f"<@{discord_id}>'s character:", embed=embed)
        conn.close()
    else:
        await ctx.send('Could not connect to database!')
        return


