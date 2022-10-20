import time
from typing import List
import random
import operator
import psycopg2

import discord
from discord.ext import commands
from pytz import timezone

intents = discord.Intents().default()
intents.members = True
bot = commands.Bot(command_prefix='$', intents=intents)

def run(TOKEN):
    bot.run(TOKEN)

from bot.database import *

ROLES = {"t", "h", "m", "c", "r", "d"}
ROLES_FULL = {"t": "tank", "h": "healer", "m": "melee", "c": "caster", "r": "ranged", "d": "dps"}
RAID_TYPES = ["BA", "DRN", "DRS"]
PARTY_SIZE = 8
MAX_PARTIES = {"BA": 7, "DRN": 3, "DRS": 6}
REQ_ROLES_PER_PARTY = {"BA": "thh", "DRN": "tcr", "DRS": "tthhcr"}

raids = []
raiders = []

class Raider:
    def __init__(self, raider_id, discord_id, character_name, roles, preferred_role, 
                 notoriety, party_lead, reserve, duelist):
        self.id = (int) raider_id
        self.name = name
        self.discord_id = (int) discord_id
        self.noto = (int) notoriety
        self.roles = list(roles)
        self.preferred_role = preferred_role
        self.party_lead = (boolean) party_lead
        self.reserve = (boolean) reserve
        self.duelist = (boolean) duelist
    
    def __str__(self):
        return self.character_name
    
    def add_roles(self, role_string: str) -> bool:
        """Adds roles separated by commas, a la "tank,dps,caster". 
           Registering yourself as DPS simply means you have no responsibilities;
           it does not refer to red classes."""
        role_string = role_string.lower()
        role_list = role_string.split(",")
        for x in role_list:
            if x in ROLES_FULL:
                self.roles.add(x[0])
            elif x in ROLES:
                self.roles.add(x)
            else:
                print(x + " is not a valid role.")
        self.roles = set(self.roles)
        self.roles = list(self.roles)
        self.roles = self.roles.sort()
        role_string = ''.join(map(str,list))

        conn = create_connection()
        update_raider(conn, "roles", role_string, self.id)
        conn.commit()
        conn.close()
        self.display_roles()

    def display_roles(self):
        role_string = self.name + " is registered as:"
        for x in role_list:
             role_string += " " + ROLES_FULL[x]
        print(role_string)

    def remove_roles(self, role_string: str) -> bool:
        """Removes roles separated by commas, a la "melee,caster"."""
        role_string = role_string.lower()
        role_list = role_string.split(",")
        self.roles = set(self.roles)
        for x in role_list:
            if x in ROLES_FULL:
                self.roles.discard(x[0])
            elif x in ROLES:
                self.roles.discard(x)
            else:
                print(x + " is not a valid role.")
        self.roles = list(self.roles)
        self.roles = self.roles.sort()
        role_string = ''.join(map(str,list))

        conn = create_connection()
        update_raider(conn, "roles", role_string, self.id)
        conn.commit()
        conn.close()
        self.display_roles()
    
    def set_preferred_role(self, role_string: str):
        """Set preferred role.  Used as party lead or raid host."""
        role_string = role_string.lower()
        if role_string in ROLES_FULL:
            self.preferred_role = role_string
        elif role_string in ROLES:
            self.preferred_role = role_string
        conn = create_connection()
        update_raider(conn, "preferred_role", self.preferred_role[0], self.id)
        conn.commit()
        conn.close()

    def increase_noto(self):
        self.noto = self.noto + 1
        conn = create_connection()
        update_raider(conn, "notoriety", self.noto, self.id)
        conn.commit()
        conn.close()
        return self.noto

    def reset_noto(self):
        self.noto = 0
        conn = create_connection()
        update_raider(conn, "notoriety", self.noto, self.id)
        conn.commit()
        conn.close()
        print("Notoriety for " + self.name + " has been reset.")
    
    def get_past_raids(self):
        pass

class Raid:
    def __init__(self, raid_type: str, host_id: int, organiser_id: int, raid_time: int) -> bool:
        """Initialises a raid event."""
        raid_type = raid_type.upper()
        if raid_type in RAID_TYPES:
            self.raid_type = raid_type
            self.req_roles = REQ_ROLES_PER_PARTY[self.raid_type]
        else:
            return False

        self.host_id = host_id
        self.organiser = organiser_id
        
        self.required_party_members = [host_id]

        # this will be sequential in the DB though
        self.raid_id = int(time.time())
        
        return True

    def build_roster(self):
        """Builds the list of everyone signed up for the raid."""

        raiders = []
        raiders_raw = get_raiders_by_raid_id(self.raid_id)

        for raider in raiders_raw:
            raiders.append(make_raider_from_db(raider))

        participants = []
        reserves = []
        party_leads = []
        tanks = []
        healers = []
        casters = []
        ranged = []
        parties = []
        active_players = []

        for raider in raiders:
            if raider.reserve:
                reserves.append(raider.discord_id)
            else:
                participants.append(raider.discord_id)
        
        # Raid host needs to participate.
        # TODO: logic to designate certain people as mandatory and distribute them as desired?
        if self.host_id not in self.required_party_members:
            self.required_party_members.append(self.host_id)
        
        # Randomise order
        participants.shuffle()
        reserves.shuffle()
        
        if (len(participants) // PARTY_SIZE) < self.min_parties:
            print("You have " + len(participants) + "participants, which cannot form enough parties.")
        
        # Now add each of the participants to applicable lists.
        for raider_id in participants:
            raider = get_raider_by_id(raider_id)
            if raider.party_lead:
                party_leads.append(raider_id)
            if "tank" in raider.roles:
                tanks.append(raider_id)
            if "healer" in raider.roles:
                healers.append(raider_id)
            # Only for Delubrum Reginae
            if self.raid_type != "BA":
                if "caster" in raider.roles:
                    casters.append(raider_id)
                if "ranged" in raider.roles:
                    ranged.append(raider_id)
        
        # Register the participant and remove them from organisational lists.
        def register_participant(self, raider_id: int):
            active_players.append(raider_id)
            if raider_id in required_party_members:
                participants.remove(raider_id)
            if raider_id in participants:
                participants.remove(raider_id)
            if raider_id in reserves:
                reserves.remove(raider_id)
            if raider_id in tanks:
                tanks.remove(raider_id)
            if raider_id in healers:
                healers.remove(raider_id)
            # Only for Delubrum Reginae
            if self.raid_type != "BA":
                if raider_id in casters:
                    casters.remove(raider_id)
                if raider_id in ranged:
                    ranged.remove(raider_id)
        
        # Start building parties.  Party leads get dibs on role.
        for i in range(MAX_PARTIES[self.raid_type]):
            while len(party_leads) > 0:
                temp = party_leads.pop()
                parties[i] = Party(temp)
                register_participant(temp)
                
        if self.host.discord_id not in active_players:
            parties[0].add(self.host.discord_id)
            register_participant(self.host.discord_id)

# Fill tanks and healers first. Empty slots per party are fine; host can consolidate.            
        for party in parties:
            while len(tanks) > 0 and party.current_roles.count("t") < self.req_roles.count("t"):
                temp = tanks.pop()
                party.add(temp, "t")
                register_participant(temp)
            while len(healers) > 0 and party.current_roles.count("h") < self.req_roles.count("h"):
                temp = healers.pop()
                party.add(temp, "h")
                register_participant(temp)

# Now casters and ranged.
        for party in parties:
            while len(casters) > 0 and party.current_roles.count("c") < self.req_roles.count("c"):
                temp = casters.pop()
                party.add(temp, "c")
                register_participant(temp)
            while len(ranged) > 0 and party.current_roles.count("r") < self.req_roles.count("r"):
                temp = ranged.pop()
                party.add(temp, "r")
                register_participant(temp)

# Stop when it's full.
        for party in parties:
            party_has_room = True
            while len(participants) > 0 and party_has_room:
                temp = participants.pop()
                party_has_room = party.add(temp, "d")
                # Only remove them if they were added successfully.
                if party_has_room:
                    register_participant(temp)

            while len(reserves) > 0 and party_has_room:
                temp = reserves.pop()
                party_has_room = party.add(temp, "d")
                # Only remove them if they were added successfully.
                if party_has_room:
                    register_participant(temp)
        
        self.roster = Roster(self.raid_id, parties)

        return self.roster

class Party:
    def __init__(self, lead_id):
        self.lead_id = lead_id
        self.members = []
        
        add(self.lead_id)
    
    def add(self, member_id: int, role: str="") -> bool:
        if len(self.members) < PARTY_SIZE:
            if role == "":
                temp = get_raider_by_id(member_id)
                self.members.append(PartyMember(member_id, temp.preferred_role))
                return True
            elif role in ROLES:
                self.members.append(PartyMember(member_id, role))
                return True
            else:
                return False
        else:
            return False
    
    def __str__(self):
        temp_string = "LEAD: "
        for member in self.members:
            temp_string = temp_string + member.__str__() + "\n"
        return temp_string
    
    def current_roles(self) -> str:
        role_string = ""
        for member in members:
            role_string += member.role[0]
        return role_string

class PartyMember:
    def __init__(self, raider_id: int, role: str):
        self.me = get_raider_by_id(raider_id)
        self.role = role
    
    def __str__(self):
        return self.me.character_name + " " + self.role[0] 

class Roster:
    def __init__(self, raid_id: int, parties: List[int], duelist_id=0):
        self.raid = get_raid_by_id(raid_id)
        self.parties = members.copy()
        self.roles_str = roles_str
        self.duelist = get_raider_by_id(duelist_id)

    def print_roster(self):
        for party in parties:
            print(party)
            print("------")
    
    def select_duelist(self) -> Raider:
        """Chooses a duelist for DRS. Cannot be the raid host."""
        duelists = []
        
        if self.raid.raid_type == "DRS":
            for party_member in self.party_members:
                if party_member.duelist and party_member != self.raid.host:
                    duelists.append(party_member)
           
            # We don't want party order to matter.
            duelists.shuffle()

            # Increasing noto will refresh from the database :)
            for raider in duelists:
                raider.increase_noto()
           
            duelists.sort(key=operator.attrgetter('noto'))
           
            self.duelist = duelists[-1]
            self.duelist.reset_noto()
           
            return self.duelist

def make_raider_from_db(conn, raider_id: int, discord_id: int):
    """Given either the raider_id or the discord id, read from the database
       and parse as a Raider. One of the two ids should be zero."""
    if discord_id > 0:
        raider_id = (int) get_raider_id_by_discord_id(conn, discord_id)
    attributes = get_raider_by_id(conn, raider_id)
    raider = Raider(attributes[0], attributes[1], attributes[2], attributes[3],
        attributes[4], attributes[5], attributes[6], attributes[7], attributes[8])
    return raider


