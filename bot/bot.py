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

import os

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='~', intents=intents)

def run(TOKEN):
    bot.run(TOKEN)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.add_cog(Bozja(bot))
    await bot.add_cog(Eureka(bot))
    await bot.add_cog(Forays(bot))

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
weathers["Zadnor"] = {"Rain", "Wind"}

class Bozja(commands.Cog):
    """Commands specific for Bozja/Save the Queen areas."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='bozjaforecast', help='Bozja Forecast. Shows more windows than regular forecast.')
    async def forecast_bozja(self, ctx):
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
    
    @commands.command(name='fragments', help='Lists what fragments drop where.')
    async def frags(self, ctx):

        bsf_embed = discord.Embed(title="Bozjan Southern Front fragments", 
                    description="⛈️ sprites (weather); 🐹 wildlife; 💀 undead (night only); ⭐ star ranks",
                    color=discord.Color.dark_gold())
        bsf_embed.add_field(name="**ZONE ONE** reflect during **thunder**", 
                  value="🐹 Skill (basic essences) \n" \
                        "⛈️💀 Preparation (Phoenix, Potion) \n" \
                        "⭐ Caution (Manawall, Cure 3, Incense, etc)", inline=False)
        bsf_embed.add_field(name="**ZONE TWO** reflect during **dust** or **wind**", 
                  value="🐹 Awakening (Profane, Irregular, basic essences) \n" \
                        "⛈️💀 Care (Reraiser, Potion Kit, Ether Kit) \n" \
                        "⭐ Ingenuity (Spellforge, Steelsting, Dispel, etc)", inline=False)
        bsf_embed.add_field(name="**ZONE THREE** reflect during **wind** or **dust**", 
                  value="🐹 Compassion (Cure 2, Cure 4, Arise, Medikit) \n" \
                        "⛈️💀 Support (Reflect, Stoneskin, Bravery)\n" \
                        "⭐ Violence (Focus, Slash, Death)", inline=False)

        zad_embed = discord.Embed(title="Zadnor fragments", 
                    description="⛈️ sprites (weather); 🐹 wildlife; 💀 undead (night only); ⭐ star ranks",
                    color=discord.Color.dark_gold())
        zad_embed.add_field(name="**ZONE ONE** reflect during **wind**", 
                  value="🐹 Ferocity or Rage (Stoneskin II, Burst, Rampage) \n" \
                        "⭐⛈️ History (Lodestone)", inline=False)
        zad_embed.add_field(name="**ZONE TWO** reflect during **rain**", 
                  value="🐹 Moonlight (Light Curtain) \n" \
                        "💀 Care (Reraiser, Potion Kit, Ether Kit) \n" \
                        "⭐⛈️ Artistry (Chainspell, Assassinate)", inline=False)
        zad_embed.add_field(name="**ZONE THREE** skip reflecting", 
                  value="🐹 Desperation (Protect II, Shell II) \n" \
                        "⛈️ Support (Reflect, Stoneskin, Bravery) \n" \
                        "⭐ Inspiration (Impetus) \n" \
                        "Rank IV/V Compassion (Cure 2, Cure 4, Arise, Medikit)", inline=False)
        
        embeds = []
        embeds.append(bsf_embed)
        embeds.append(zad_embed)
        
        await ctx.send(content="Try `~reflect` or `~bozjaforecast` for help reflecting sprites.", embeds=embeds)

class Eureka(commands.Cog):
    """Commands specific to Eureka and the Baldesion Arsenal."""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='eurekaforecast', help='Eureka Forecast. Shows more windows than regular forecast.')
    async def forecast_eureka(self, ctx):
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
    
    @commands.command(name='logograms', help='Lists where to get logograms.')
    async def logograms(self, ctx):
        
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
    
    @commands.command(name='wisdoms', help="Lists standard wisdoms and ingredients.")
    async def wisdoms(self, ctx):
        wisdomList = "***Healers:*** \nPlatebearer ;)\n" \
                     "Templar -- Skirmisher + Cure II _or_ Skirmisher + Stoneskin _or_ Platebearer + Stoneskin + Cure\n" \
                     "***Tanks:*** \nGuardian -- Protect + Platebearer\n" \
                     "Indomitable -- Double Edge + Platebearer + Incense\n" \
                     "***Casters:*** \nElder -- Aetherweaver + Ordained + Magic Burst\n" \
                     "***Melee:*** \nDuelist -- Double Edge + Backstep + Bloodbath _or_ Double Edge + Skirmisher + Skirmisher\n" \
                     "***Ranged:*** \nFiendhunter -- Feint + Tranquilizer + Eagle Eye Shot\n" \
                     "Irregular -- Martialist + Skirmisher + Incense\n"
        await ctx.send(wisdomList)

    @commands.command(name='actions', help="Lists standard BA actions and ingredients.")
    async def ba_actions(self, ctx):
        embed = discord.Embed(title="Action Crafting", 
                description="Remember the more mnemes, the more broken trays.",
                color=discord.Color.dark_gold())
        embed.add_field(name="***General***", 
              value="Spirit of the Remembered -- Aetherweaver + Martialist + Platebearer\n" \
                    "Death -- Raise + Dispel\n" \
                    "Focus -- Skirm + Bloodbath\n" \
                    "Reflect -- Ordained + Protect + Shell\n" \
                    "Shell -- Protect + Esuna", inline=False)
        embed.add_field(name="***DPS***", 
              value="Perception -- Breathtaker x2\n" \
                    "Rapid Recast -- Dispel + Esuna", inline=False)
        embed.add_field(name="***Healers***", 
              value="Bravery -- Skirmisher + Guardian + Ordained\n" \
                    "Refresh -- Aetherweaver + Ordained + Cure II\n" \
                    "Sacrifice -- Magic Burst + Raise + Esuna", inline=False)
        embed.add_field(name="***Tanks***", 
              value="Catastrophe -- Spirit Dart x3 _or_ Bloodbath + Bloodbath\n" \
                    "Cure III -- Cure II x2 _or_ Ordained + Cure + Cure _or_ Ordained + Bloodbath", inline=False)
        embed.set_footer(text=f"Keeping Spirit of the Remembered up is good both in BA and solo!")

        await ctx.send(embed=embed)


class Forays(commands.Cog):
    """Commands for both types of Adventuring Foray."""
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='forecast', help='Forecast overview for adventuring forays.')
    async def forecast(self, ctx):
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

    @commands.command(name='reflect', help='Explains how to reflect farm')
    async def reflect(self, ctx):
        embed = discord.Embed(title="Reflect farming in a nutshell", 
                description="How to kill sprites and influence people.",
                color=discord.Color.dark_gold())
        embed.add_field(name="**General**", inline=False,
              value="Reflect L and Lost Reflect prevent you from taking certain damage and send it back to the caster." \
                    "  Incidentally, everything a Sprite does can be reflected.  When reflect farming, " \
                    "first, find a group of sprites. Stand a comfortable distance away from them. " \
                    "They aggro on casting and will probably gank you otherwise. \n" \
                    "Remove all your gear, cast Reflect on yourself, then move slightly closer and start pulling. " \
                    "Recasting Reflect can pull them pretty well by itself. \n" \
                    "Recast Reflect every time the buff hits 3 seconds. Earlier is better. \n" \
                    "Done right, they will take mega damage and you will take zero.")
        embed.add_field(name="**Eureka**", inline=False,
              value="Reflect is made through Protect, Shell, and Wisdom of the Ordained. " \
                    "You can powerlevel like this by the Carbonatite Quarry in Pyros.")
        embed.add_field(name="**Bozja**", inline=False,
              value="Lost Reflect comes from Forgotten Fragments of Support. \n" \
                    "Spirit of the Guardian triples the buff duration, but it increases your defense " \
                    "so each reflected auto attack does less damage. Pick your poison.")

        embed.set_footer(text=f"Sprites aggro on cast, which includes Raise. Watch your step.")

        await ctx.send(embed=embed)



@bot.command(name='fish', help='Updates status with a random fish.')
async def fish(ctx):
    fishies = ("the Ambitious Angler", "of Dragons Deep", "Odin before Namitaro", 
               "Charibenet escape", "the Pie for Paikiller", "a total lack of Sea Butterfly",
               "for Green Prismfish", "for Sculptors", "yet Unconditional", "the Ruby Dragon", 
               "Egg prep", "scramble some Egg Salad", "for Mora Tecta", "to Triple Hook Dafu")
    fish = random.choice(fishies)
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=fish))
    options = [
        f"Do raiders fish between raids, or fishers raid between fish?",
        f"I'd never Chum cancel you, {ctx.message.author.mention}.",
        f"I was feeling pretty Irregular, but now I'm a Blue Corpse.",
        f"Aetherial Stabilizers are pretty Problematicus.",
        f"Mud Golem?  No, I'm the Slime King.",
        f"Cassie hates Master Casters; text it.",
        f"It's _always_ time for crab.",
        f"If it's Dawon to bring my gathering gear to Bozja, I don't wanna be right.",
        f"They call me the Unforgiven because I still haven't dropped a Blitzring.",
        f"You do Castrum with 48; I do it with 4; we are not the same.",
        f"Notoriety does not apply to Cinder Surprise.",
        f"Stop Lyon; field notes aren't real."
    ]
    response = random.choice(options)
    await ctx.send(response)
    time.sleep(2)
