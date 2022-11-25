import time
from typing import List
import random
import operator
import psycopg2
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
weathers["Bozjan Southern Front"] = {"Dust Storms", "Wind"}
weathers["Zadnor"] = {"Rain"}

@bot.command(name='forecast', help='Forecast')
async def forecast(ctx):
    zones = ("Eureka Pagos", "Eureka Pyros", "Bozjan Southern Front", "Zadnor")
    numWeather = 5

    goalWeathers = []
    for zone in zones:
       forecast = ffxivweather.forecaster.get_forecast(place_name=zone, count=numWeather)
       for weather, start_time in forecast:
          fmt2 = datetime.timestamp(start_time)
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
          fmt2 = datetime.timestamp(start_time)
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
          fmt2 = datetime.timestamp(start_time)
          if weather["name_en"] in weathers[zone]:
             goalWeathers.append(Weather(zone, weather["name_en"], fmt2))
    
    goalWeathers = sorted(goalWeathers, key=operator.attrgetter("time"))
    finalString = f""
    for weather in goalWeathers:
        finalString += f'{weather.zone} - {weather.name} - <t:{weather.time:.0f}:R> - \<t:{weather.time:.0f}:R\>\n'
    await ctx.send(finalString)

@bot.command(name='fish', help='Updates status with a random fish.', hidden=True)
async def fish(ctx):
    fishies = ("for Mora Tecta", "for Green Prismfish", "for Sculptors", "for Egg Salad", "for the Unconditional", "Charibenet escape", "to Prize Catch Triple Hook Dafu")
    fish = random.choice(fishies)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=fish))
    time.sleep(2)

