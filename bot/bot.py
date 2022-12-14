import time
from typing import List
import random
import operator
import re

import discord
from discord.ext import commands
from pytz import timezone
import datetime
import ffxivweather

import dotenv
import os

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='~', intents=intents)

PLANNING_CHANNEL     = os.getenv('PLANNING_DRS')
ANNOUNCEMENT_CHANNEL = os.getenv('ANNOUNCING_DRS')
RUN_REQUEST_CHANNEL = os.getenv('RUN_REQUEST_CHANNEL')

def run(TOKEN):
    bot.run(TOKEN)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

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

class Weather:
    def __init__(self, zone, name, time):
        self.zone = zone
        self.name = name
        self.time = time

weathers = {}
weathers["Eureka Anemos"] = {"Gales"}
weathers["Eureka Pagos"] = {"Fog", "Blizzards"}
weathers["Eureka Pyros"] = {"Blizzards", "Heat Waves"}
weathers["Bozjan Southern Front"] = {"Dust Storms", "Wind", "Thunder"}
weathers["Zadnor"] = {"Rain"}

@bot.command(name='forecast', help='Forecast')
async def forecast(ctx):
    zones = ("Eureka Pagos", "Eureka Pyros", "Bozjan Southern Front", "Zadnor")
    numWeather = 5

    goalWeathers = []
    for zone in zones:
       forecast = ffxivweather.forecaster.get_forecast(place_name=zone, count=numWeather)
       for weather, start_time in forecast:
          fmt2 = time.mktime(start_time.timetuple()) + start_time.microsecond/1e6
          if weather["name_en"] in weathers[zone]:
             goalWeathers.append(Weather(zone, weather["name_en"], fmt2))
    
    goalWeathers = sorted(goalWeathers, key=operator.attrgetter("time"))
    finalString = f""
    for weather in goalWeathers:
        finalString += f'{weather.zone} - {weather.name} - <t:{weather.time:.0f}:R> - \<t:{weather.time:.0f}:R\>\n'
    await ctx.send(finalString)

@bot.command(name='eurekaforecast', help='Eureka Forecast. Shows more windows than regular forecast.')
async def forecast_eureka(ctx):
    zones = ("Eureka Anemos", "Eureka Pagos", "Eureka Pyros")
    numWeather = 15
    goalWeathers = []
    
    for zone in zones:
       forecast = ffxivweather.forecaster.get_forecast(place_name=zone, count=numWeather)
       for weather, start_time in forecast:
          fmt2 = time.mktime(start_time.timetuple()) + start_time.microsecond/1e6
          if weather["name_en"] in weathers[zone]:
             goalWeathers.append(Weather(zone, weather["name_en"], fmt2))
    
    goalWeathers = sorted(goalWeathers, key=operator.attrgetter("time"))
    finalString = f""
    for weather in goalWeathers:
        finalString += f'{weather.zone} - {weather.name} - <t:{weather.time:.0f}:R> - \<t:{weather.time:.0f}:R\>\n'
    await ctx.send(finalString)

@bot.command(name='bozjaforecast', help='Bozja Forecast. Shows more windows than regular forecast.')
async def forecast_bozja(ctx):
    zones = ("Bozjan Southern Front", "Zadnor")
    numWeather = 15
    goalWeathers = []
    
    for zone in zones:
       forecast = ffxivweather.forecaster.get_forecast(place_name=zone, count=numWeather)
       for weather, start_time in forecast:
          fmt2 = time.mktime(start_time.timetuple()) + start_time.microsecond/1e6
          if weather["name_en"] in weathers[zone]:
             goalWeathers.append(Weather(zone, weather["name_en"], fmt2))
    
    goalWeathers = sorted(goalWeathers, key=operator.attrgetter("time"))
    finalString = f""
    for weather in goalWeathers:
        finalString += f'{weather.zone} - {weather.name} - <t:{weather.time:.0f}:R> - \<t:{weather.time:.0f}:R\>\n'
    await ctx.send(finalString)

@bot.command(name='fish', help='Updates status with a random fish.', hidden=True)
async def fish(ctx):
    fishies = ("for Mora Tecta", "for Green Prismfish", "for Sculptors", "for Egg Salad", "for the Unconditional", "Charibenet escape", "to Triple Hook Dafu")
    fish = random.choice(fishies)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=fish))
    time.sleep(2)

@bot.command(name='fragments', help='Lists what fragments drop where.')
async def bozja_frags(ctx):
    fragList = "?????? sprites (weather); ???? wildlife; ???? undead (night only); ??? star ranks. Higher ranks have better drops! \n \n" \
               "***Bozja Southern Front:*** \n" \
               "**ZONE ONE** reflect during **thunder** \n" \
               "> ???? Skill (basic essences) \n" \
               "> ?????????? Preparation (Phoenix, Potion) \n" \
               "> ??? Caution (Manawall, Cure 3, Incense, etc) \n" \
               "**ZONE TWO** reflect during **dust** or **wind** \n" \
               "> ???? Awakening (Profane, Irregular, basic essences) \n" \
               "> ?????????? Care (Reraiser, Potion Kit, Ether Kit) \n" \
               "> ??? Ingenuity (Spellforge, Steelsting, Dispel, etc) \n" \
               "**ZONE THREE** reflect during **wind** or **dust** \n" \
               "> ???? Compassion (Cure 2, Cure 4, Arise, Medikit) \n" \
               "> ?????????? Support (Reflect, Stoneskin, Bravery)\n" \
               "> ??? Violence (Focus, Slash, Death) \n" \
               "\n***Zadnor:*** \n" \
               "**ZONE ONE** reflect during **wind** \n" \
               "> ???? Ferocity or Rage (Stoneskin II, Burst, Rampage) \n" \
               "> ????????? History (Lodestone)\n" \
               "**ZONE TWO** reflect during **rain** \n" \
               "> ???? Moonlight (Light Curtain) \n" \
               "> ???? Care (Reraiser, Potion Kit, Ether Kit) \n" \
               "> ????????? Artistry (Chainspell, Assassinate) \n" \
               "**ZONE THREE** \n" \
               "> ???? Desperation (Protect II, Shell II) \n" \
               "> ?????? Support (Reflect, Stoneskin, Bravery) \n" \
               "> ??? Inspiration (Impetus) \n" \
               "> Rank IV/V Compassion (Cure 2, Cure 4, Arise, Medikit)"
    await ctx.send(fragList)

@bot.command(name='logograms', help='Lists where to get logograms.')
async def logograms(ctx):
    logogramList = "Reminder that you can buy things on the marketboard, too. \n" \
                   "**Conceptual Logograms** -- Aetherweaver, Martialist, Platebearer, Backstep, Cure, Incense, Paralyze \n" \
                   "> Sprite Island during showers/thunderstorms\n" \
                   "**Fundamental Logograms** -- Esuna, Raise, Feint, Tranquilizer, Protect\n" \
                   "> Sprite Island during gloom/snow\n" \
                   "**Offensive Logograms** -- Skirmisher, Bloodbath \n" \
                   "> Hydatos Adapted lv 64 Snowstorm Sprites \n> bunnies\n" \
                   "**Protective Logograms** -- Guardian, Spirit of the Remembered\n" \
                   "> bunnies\n" \
                   "**Curative Logograms** -- Ordained, Cure L II \n" \
                   "> bunnies\n" \
                   "**Tactical Logograms** -- Featherfoot, Stealth \n" \
                   "> moist boxes\n" \
                   "**Inimical Logograms** -- Spirit Dart, Dispel\n" \
                   "> Pyros Adapted Snowstorm/Thunderstorm/Typhoon Sprites\n> bunnies\n" \
                   "**Mitigative Logograms** -- Shell, Stoneskin\n" \
                   "> Pyros Adapted Lv 46 Thunderstorm Sprites (sync down in Aetolus's FATE circle)\n" \
                   "**Obscure Logograms** -- Magic Burst, Eagle Eye Shot, Double Edge, Breathtaker \n" \
                   "> Baldesion Arsenal\n> Crystal Claws"
    await ctx.send(logogramList)

