import time
from typing import List
import random
import operator
import psycopg2
import re

import discord
from discord.ext import commands
from pytz import timezone

import dotenv
import os

import ffxivweather
import datetime

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='~', intents=intents)

PLANNING_CHANNEL     = os.getenv('PLANNING_DRS')
ANNOUNCEMENT_CHANNEL = os.getenv('ANNOUNCING_DRS')
RUN_REQUEST_CHANNEL = os.getenv('RUN_REQUEST_CHANNEL')

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
    embed.set_footer(text=f"Dog Ponderer #{raider.id}")
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

@bot.command(name='changeroles', help="Changes your roles in the database")
async def changeroles(ctx, roles: str, preferred_role='d'):
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

@bot.command(name='drs', help='Creates a DRS run with the given parameters: '
                              'name date (format y-m-d) time (format HH:MM) '
                              'timezone (optional, default UTC)\n'
                              'and then \@ing your cohost if desired', hidden=True)
async def host_drs(ctx, date, start_time, user_timezone, cohost):
    if int(ctx.channel.id) != RUN_REQUEST_CHANNEL:
        await ctx.send(f"Get thee to <#{RUN_REQUEST_CHANNEL}> ;)")
        return

    conn = create_connection()
    if conn is not None:
        try:
            tz = timezone(user_timezone)
        except Exception:
            conn.close()
            tz_link = "https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568"
            embed = discord.Embed(description=f"A link to all possible timezones can be found [here]({tz_link})",
                                  color=discord.Color.dark_gold())
            await ctx.send(f"Unknown timezone {user_timezone}, use format like 'Europe/Amsterdam'", embed=embed)
            return

        try:
            y, m, d = date.split("-")
            hour, minute = start_time.split(":")
            dt_obj = datetime(int(y), int(m), int(d), int(hour), int(minute))
            dt_obj = tz.normalize(tz.localize(dt_obj))
        except Exception:
            conn.close()
            await ctx.send(f"Could not parse date and/or time, make sure to format like this: "
                           f"yyyy-mm-dd hh:mm (in 24 hour format)")
            return
        
        if len(cohost) > 0:
            organiser_id = int(cohost[2:-1])
        else:
            organiser_id = 0
        
        ev_id = create_raid(conn, RAID_TYPES.index(raid_type), host_discord, organiser_id, dt_obj)

        try:
            raid = make_raid_from_db(conn, ev_id)
        except Exception:
            conn.close()
            await ctx.send(f'Failed to create {ev_id}.')
            return
        embed = make_raid_embed(raid)
        # Check if we have an event channel
#        channel = PLANNING_CHANNEL
#        message = await ctx.guild.get_channel(int(channel)).send(embed=embed)
#            new_embed = make_event_embed(event, ctx.guild, False)
#            new_embed.add_field(name="**Original post**", value=f"[link]({message.jump_url})", inline=False)
#            await ctx.send(embed=new_embed)
#        else:
#            message = await ctx.send(embed=embed)
#        update_raid(conn, "planning_link", message.jump_url, ev_id)
#        await message.add_reaction("🔛")
        conn.close()
        return
    else:
        await ctx.send('Could not connect to database. Need connection to create and save events.')
        return


@bot.command(name='forecast', help='Forecast')
async def check_weather(ctx):
    zones = ("Eureka Anemos", "Eureka Pagos", "Eureka Pyros", "Bozjan Southern Front")
    weathers = {}
    weathers["Eureka Anemos"] = {"Gales"}
    weathers["Eureka Pagos"] = {"Fog", "Blizzards"}
    weathers["Eureka Pyros"] = {"Blizzards", "Heat Waves"}
    weathers["Bozjan Southern Front"] = {"Dust Storms", "Wind"}
    numWeather = 5
    goalWeathers = []
    
    class Weather:
        def __init__(self, zone, name, time):
           self.zone = zone
           self.name = name
           self.time = time
    
    for zone in zones:
       forecast = ffxivweather.forecaster.get_forecast(place_name=zone, count=numWeather)
       for weather, start_time in forecast:
          fmt2 = datetime.timestamp(start_time)
          if weather["name_en"] in weathers[zone]:
             goalWeathers.append(Weather(zone, weather["name_en"], fmt2))
    
    goalWeathers = sorted(goalWeathers, key=operator.attrgetter("time"))
    for weather in goalWeathers:
        await ctx.send(f'{weather.zone} - {weather.name} - <t:{weather.time:.0f}:R> - \<t:{weather.time:.0f}:R\>')

