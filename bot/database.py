from typing import List
import psycopg2
from psycopg2 import Error
from psycopg2 import sql
import os
from urllib.parse import urlparse 
from datetime import datetime

RAIDERS_COLUMNS = ["raider_id", "discord_id", "character_name", "roles", 
                 "preferred_role", "notoriety", "party_lead", "reserve", "duelist"]

RAIDS_COLUMNS   = ["raid_id", "raid_type", "host_id", "host_discord", "organiser_id", 
                   "raid_time", "planning_link", "announcement_link"]

RAID_TYPES = ["BA", "DRS"]


ROLES = {"t", "h", "m", "c", "r", "d"}
EXPAND_ROLES = {"t": "tank", "h": "healer", "m": "melee", "c": "caster", "r": "ranged", "d": "dps"}
SHORTEN_ROLES = {"tank": "t", "healer": "h", "melee": "m", "caster": "c", "ranged": "r", "dps": "d"}
PARTY_SIZE = 8
MAX_PARTIES = {"BA": 7, "DRN": 3, "DRS": 6, "N/A": 7}
REQ_ROLES_PER_PARTY = {"BA": "thh", "DRS": "tthhcr"}

raids = []
raiders = []

def create_connection():
    result = urlparse(os.getenv('DATABASE_URL'))
    USER = result.username
    PASSWORD = result.password
    DATABASE = result.path[1:]
    HOST = result.hostname
    PORT = result.port

    conn = psycopg2.connect(database=DATABASE, user=USER, password=PASSWORD, host=HOST,port=PORT)
    return conn

class Raider:
    def __init__(self, raider_id, discord_id, character_name, roles, preferred_role, 
                 notoriety, party_lead, reserve, duelist):
        self.id = int(raider_id)
        self.name = character_name
        self.discord_id = int(discord_id)
        self.noto = int(notoriety)
        self.roles = roles
        self.preferred_role = preferred_role
        self.party_lead = bool(party_lead)
        self.reserve = bool(reserve)
        self.duelist = bool(duelist)
    
    def __str__(self):
        return self.character_name

    def role_string(self):
        role_string = ""
        for x in self.roles:
             role_string += EXPAND_ROLES[x] + " "
        return role_string

def sanitize_roles(roles: str, preferred_role: str):
    roles = roles.lower()
    role_list = roles.split(",")
    roles = ""
    for x in role_list:
        if x in ROLES:           roles += x
        elif x in SHORTEN_ROLES: roles += SHORTEN_ROLES[x]
    roles = list(set(roles))
    roles.sort()
    roles = "".join(roles)

    if preferred_role in ROLES:           preferred_role = preferred_role
    elif preferred_role in SHORTEN_ROLES: preferred_role = SHORTEN_ROLES[preferred_role]
    else:                                 preferred_role = "d"

    return roles, preferred_role


def make_raid_embed(ev):
    embed = None
    if ev.raid_type == "BA":
        embed = discord.Embed(title=f"**The Baldesion Arsenal",
                          description=f"called & hosted by <@{ev.host_discord}>**",
                          color=discord.Color.dark_gold())
    elif ev.raid_type == "DRS":
        embed = discord.Embed(title=f"**Delubrum Reginae SAVAGE",
                          description=f"called & hosted by <@{ev.host_discord}>**",
                          color=discord.Color.dark_gold())
    else:
        embed = discord.Embed(title=f"**{ev.raid_type} -- {ev.host_id}",
                          description=f"Organized by **{creator_name}**",
                          color=discord.Color.dark_gold())
    if ev.organiser_id > 0:
        embed.add_field(name="**Organiser & Cat Wrangler**", value=f"<@{ev.organiser_id}>", inline=False)
    embed.add_field(name="**Time**", value=f"{ev.get_discord_time_format()} -> [Countdown]"
                                           f"({build_countdown_link(ev.timestamp)})", inline=False)
    if ev.planning_link is not None:
        embed.add_field(name="**More Details**", value=f"[link]({ev.planning_link})", inline=False)
    return embed

def make_raid_from_db(conn, raid_id: int):
    """Given the raid id, read from the database and parse as a Raid."""
    attributes = get_raid_by_id(conn, raid_id)
    raid = Raid(attributes[0], attributes[1], attributes[2], attributes[3],
        attributes[4], attributes[5], attributes[6], attributes[7])
    return raid

class Raid:
    def __init__(self, raid_id: int, raid_type: int, host_id: int, host_discord: int, 
        organiser_id: int, raid_time: datetime, planning_link: str, announcement_link: str):
        """Initialises a raid. host_discord and organiser_id both refer to discord IDs, not to DB IDs!"""
        self.raid_id = int(raid_id)
        self.raid_type = RAID_TYPES[raid_type]
        self.req_roles = REQ_ROLES_PER_PARTY[self.raid_type]
        self.host_discord = int(host_discord)
        self.organiser = int(organiser_id)
        self.planning_link = planning_link
        self.announcement_link = announcement_link

        if host_id < 1:
            conn = create_connection()
            self.host_id = get_raider_id_by_discord_id(conn, self.host_discord)
            conn.close()
        else:
            self.host_id = host_id
        
        self.raid_time = raid_time
        self.required_party_members = [self.host_id]

    def get_discord_time_format(self) -> str:
        """Returns the unix epoch formatted in a way Discord automatically displays the correct timezone"""
        return "<t:" + self.raid_time.__str__() + ">"

    def build_roster(self):
        """Builds the list of everyone signed up for the raid."""

        raiders = []
        raiders_raw = get_raiders_by_raid_id(self.raid_id)

        for raider in raiders_raw:
            raiders.append(make_raider_from_db(raider, 0))

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
                reserves.append(raider.raider_id)
            else:
                participants.append(raider.raider_id)
        
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

            if raider.party_lead:                   party_leads.append(raider_id)
            if "tank" in raider.roles:              tanks.append(raider_id)
            if "healer" in raider.roles:            healers.append(raider_id)
            # Only for Delubrum Reginae
            if self.raid_type != "BA":
                if "caster" in raider.roles:        casters.append(raider_id)
                if "ranged" in raider.roles:        ranged.append(raider_id)
        
        # Register the participant and remove them from organisational lists.
        def register_participant(self, raider_id: int):
            active_players.append(raider_id)
            if raider_id in required_party_members: required_party_members.remove(raider_id)
            if raider_id in participants:           participants.remove(raider_id)
            if raider_id in reserves:               reserves.remove(raider_id)
            if raider_id in tanks:                  tanks.remove(raider_id)
            if raider_id in healers:                healers.remove(raider_id)
            # Only for Delubrum Reginae
            if self.raid_type != "BA":
                if raider_id in casters:            casters.remove(raider_id)
                if raider_id in ranged:             ranged.remove(raider_id)
        
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
        raider_id = get_raider_id_by_discord_id(conn, discord_id)
        raider_id = int(''.join(map(str, raider_id)))
    attributes = get_raider_by_id(conn, raider_id)
    raider = Raider(attributes[0], attributes[1], attributes[2], attributes[3],
        attributes[4], attributes[5], attributes[6], attributes[7], attributes[8])
    return raider

def initialize_db_with_tables():
    """initialise database"""
    conn = create_connection()
    success = True
    commands = (
        """
        CREATE TABLE IF NOT EXISTS raiders (
            raider_id SERIAL PRIMARY KEY,
            discord_id BIGINT NOT NULL UNIQUE,
            character_name TEXT NOT NULL UNIQUE,
            roles TEXT DEFAULT 'd',
            preferred_role CHAR DEFAULT 'd',
            notoriety SMALLINT DEFAULT 0,
            party_lead BOOLEAN DEFAULT FALSE,
            reserve BOOLEAN DEFAULT FALSE,
            duelist BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS raids (
            raid_id SERIAL PRIMARY KEY,
            raid_type SMALLINT NOT NULL,
            host_id INTEGER NOT NULL,
            host_discord BIGINT NOT NULL,
            organiser_id BIGINT,
            raid_time TIMESTAMPTZ NOT NULL,
            planning_link TEXT,
            announcement_link TEXT,
            FOREIGN KEY (host_id)
                REFERENCES raiders(raider_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS signups (
            raid_id INTEGER NOT NULL,
            raider_id INTEGER NOT NULL,
            PRIMARY KEY (raid_id, raider_id)
            FOREIGN KEY (raid_id)
                REFERENCES raids (raid_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (raider_id)
                REFERENCES raiders (raider_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """,
        """CREATE TABLE IF NOT EXISTS channels (
            name VARCHAR (6) NOT NULL UNIQUE,
            channel_id BIGINT NOT NULL UNIQUE
        )
        """)

    try:
        cur = conn.cursor()
        for command in commands:
            cur.execute(command)
        cur.close()
        conn.commit()
    except (Exception, Error) as error:
        success = False
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn is not None:
            conn.close()
    return success

def create_raider(conn, discord_id: int, character_name: str, roles: str, preferred_role='d'):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO raiders (discord_id, character_name, roles, preferred_role) VALUES (%s, %s, %s, %s)",
            (discord_id, character_name, roles, preferred_role))
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if cur is not None:
            cur.close()

def create_raid(conn, raid_type: int, host_discord, organiser_id, raid_time):
    raid_id = 0
    if raid_type > len(RAID_TYPES): return raid_id
    host_id = get_raider_id_by_discord_id(host_discord)
    if host_id is None: return raid_id
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO raids (raid_type, host_id, host_discord, organiser_id, raid_time) VALUES (%s, %s, %s, %s, %s) RETURNING raid_id",
            (raid_type, host_id, host_discord, organiser_id, raid_time))
        raid_id = cursor.fetchone()[0]
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if cur is not None:
            cur.close()
            return raid_id

def get_raid_by_id(conn, raid_id: int):
    """Find the raid given id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raids WHERE raid_id=%s", (raid_id,))
    return cur.fetchone()

def get_raids_by_host_id(conn, host_id: int):
    """Find the raid given host DB id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raids WHERE host_id=%s", (host_id,))
    return cur.fetchall()

def get_raider_by_id(conn, raider_id: int):
    """Find the player given DB id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raiders WHERE raider_id=%s", (raider_id,))
    return cur.fetchone()

def get_raider_id_by_discord_id(conn, discord_id: int):
    """Find the player given Discord id"""
    cur = conn.cursor()
    cur.execute("SELECT raider_id FROM raiders WHERE discord_id=%s", (discord_id,))
    return cur.fetchone()

def get_raiders_by_raid_id(conn, raid_id: int):
    """Find the participants of a raid given the id"""
    raiders = []
    try:
        cur = conn.cursor()
        cur.execute("SELECT raider_id FROM signups WHERE raider_id=%s", (raider_id,))
        raider_ids = cur.fetchall()
        raiders = []
        for raider in raider_ids:
            get_raider_by_id(conn, raider)
            raiders.append(cur.fetchone())
    except (Exception, Error) as error:
        print("Error getting raiders by raid ID", error)
    finally:
        if cur is not None:
            cur.close()
    return raiders

def update_raider(conn, field, value, raider_id):
    if field in RAIDERS_COLUMNS:
        query = sql.SQL("UPDATE {table} SET {field} = %s WHERE raider_id = %s").format(
                table=sql.Identifier('raiders'),
                field=sql.Identifier(field))
        cur = conn.cursor()
        cur.execute(query,(value, raider_id))
        conn.commit()
    else:
        print(f"{field} not in raiders columns")
    if cur is not None:
        cur.close()

def update_raid(conn, field, value, raid_id):
    if field in RAIDS_COLUMNS:
        query = sql.SQL("UPDATE {table} SET {field} = %s WHERE raid_id = %s").format(
                table=sql.Identifier('raids'),
                field=sql.Identifier(field))
        cur = conn.cursor()
        cur.execute(query,(value, raider_id))
        conn.commit()
    else:
        print(f"{field} not in raids columns")
    if cur is not None:
        cur.close()

def get_upcoming_raids(conn):
    """Finds raids that have not happened yet."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT * from raids WHERE raid_time >= now();")
    except (Exception, Error) as error:
        print("Error getting upcoming raids.", error)
    return cur.fetchmany(5)

def build_countdown_link(timestamp):
    dt_obj = datetime.fromtimestamp(timestamp, tz=timezone("UTC"))
    link = f"https://www.timeanddate.com/countdown/generic?iso={dt_obj.year}{dt_obj.month:02}{dt_obj.day:02}" \
           f"T{dt_obj.hour:02}{dt_obj.minute:02}{dt_obj.second:02}&p0=0&font=cursive"
    return link
