import time
from typing import List
import random
import operator

ROLES = {"tank", "healer", "melee", "caster", "ranged", "dps"}
RAID_TYPES = {"BA", "DRN", "DRS"}
PARTY_SIZE = 8
MAX_PARTIES = {"BA": 7, "DRN": 3, "DRS": 6}
REQ_ROLES_PER_PARTY = {"BA": "thh", "DRN": "tcr", "DRS": "tthhcr"}

raids = []
raiders = []

class Raider:
    def __init__(self, name: str, discord_id: int, role_string="dps"):
        """A potential raid participant. noto is the number of times in a row
        the person has wanted to duel but was not chosen. reserve reduces their
        priority for being chosen in a party until they turn that off."""
        self.character_name = name
        self.discord_id = discord_id
        self.noto = 0
        self.raids = {}
        self.roles = {}
        self.add_roles(role_string)
        self.reserve = False
        self.duelist = False
        self.party_lead = False
        self.DRS_comfort = 0
    
    def __str__(self):
        return self.character_name
    
    def add_roles(self, role_string):
        """Adds roles separated by commas, a la "tank,dps,caster". Everyone is a DPS.
        Caster and ranged are distinct roles in Delubrum Reginae."""
        role_string = role_string.lower()
        role_list = role_string.split(",")
        for x in role_list:
            if x in ROLES:
                self.roles.add(x)
            else:
                print(x + " is not a valid role.")
    
    def remove_roles(self, roles):
        """Removes roles separated by commas, a la "melee,caster"."""
        role_string = role_string.lower()
        role_list = role_string.split(",")
        for x in role_list:
            if ROLES.count(x) > 0:
                self.roles.discard(x)
            else:
                print(x + " is not a valid role.")
    
    def increase_noto(self):
        #TODO: this should increase noto in the database then copy it 
        self.noto = self.noto + 1
        return self.noto

    def reset_noto(self):
        self.noto = 0

def get_raider_by_id(raider_id: int) -> Raider:
    """Checks database for the raider in question."""
    for raider in raiders:
        if raider.discord_id == raider_id:
            return raider
    return 0

def get_raiders_by_raid_id(raid_id: int) -> List[int]:
    """Returns discord IDs of raiders participating in the raid."""
    participants = []
    
    # TODO learn postgres
    for raider in raiders:
        if raid_id in raider.raids
            participants.append(raider.discord_id)
    return participants

class Raid:
    def __init__(self, raid_type: str, host_id: int, raid_time: int, host_role: str, min_parties: int) -> int:
        """Initialises a raid event; returns the raid id, or 0 if failed."""
        raid_type = raid_type.upper()
        if raid_type in RAID_TYPES:
            self.raid_type = raid_type
            self.req_roles_per_party = REQ_ROLES_PER_PARTY[self.raid_type]
        else:
            return 0
        
        self.raid_host = get_raider_by_id(host_id)
        
        if host_role in ROLES:
            self.host_role = host_role
        else:
            return 0
        
        if min_parties < MAX_PARTIES[self.raid_type]:
            self.min_parties = min_parties
            if self.min_parties < 0:
                self.min_parties = 0
        else:
            self.min_parties = MAX_PARTIES[self.raid_type]
        
        self.raid_id = int(time.time())

    def build_roster(self) -> Roster:
        """Builds the list of everyone signed up for the raid."""

        participants = []
        reserves = []
        party_leads = []
        tanks = []
        healers = []
        casters = []
        ranged = []
        party_ids = []
        party_count = 0
        roles_str = ""
        
        raiders = get_raiders_by_raid_id(self.raid_id)

        for raider in raiders:
            if raider.reserve:
                reserves.append(raider.discord_id)
            else:
                participants.append(raider.discord_id)
        
        # Raid host needs to participate.
        # TODO: logic to designate certain people as mandatory and distribute them as desired?
        if self.raid_host not in self.required_party_members:
        self.required_party_members.append(raid.raid_host.discord_id)
        
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
            party_members.append(raider_id)
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
        
        while len(party_leads) > 0 and party_count < MAX_PARTIES[self.raid_type]:
            # First party member is party lead.
            party = [party_leads.pop()]
            register_participant(party[0])
            
            # Party lead gets randomly assigned role.
            party_lead = get_raider_by_id(party[0])
            party_comp = random.choice(party_lead.roles)
            party_comp = party_comp[0]
            
            # Check that we got the raid host in here. They have dibs on role.
            if self.raid_host.discord_id not in participants:
                party.append(self.raid_host.discord_id)
                party_comp = party_comp + self.host_role[0]
                register_participant(party[-1])
            
            while len(tanks) > 0 and party_comp.count("t") < self.req_roles_per_party.count("t"):
                party.append(tanks.pop())
                party_comp = party_comp + "t"
                register_participant(party[-1])
            
            while len(healers) > 0 and party_comp.count("h") < self.req_roles_per_party.count("h"):
                party.append(healers.pop())
                party_comp = party_comp + "h"
                register_participant(party[-1])
                
            while len(casters) > 0 and party_comp.count("c") < self.req_roles_per_party.count("c"):
                party.append(casters.pop())
                party_comp = party_comp + "c"
                register_participant(party[-1])
        
            while len(ranged) > 0 and party_comp.count("r") < self.req_roles_per_party.count("r"):
                party.append(ranged.pop())
                party_comp = party_comp + "r"
                register_participant(party[-1])
        
            while len(participants) > 0 and len(party) < PARTY_SIZE:
                party.append(participants.pop())
                party_comp = party_comp + "d"
                register_participant(party[-1])
        
            if len(party) < PARTY_SIZE and len(participants) == 0 and len(reserves) > 0:
                while len(reserves) > 0 and len(party) < PARTY_SIZE:
                    party.append(reserves.pop())
                    party_comp = party_comp + "d"
                    register_participant(party[-1])
        
            roles_str = roles_str + party_comp
            party_count++
            party.clear()
            party_comp.clear()
        
        # Melees are irrelevant; they're a dps.
        roles_str = roles_str.replace("m", "d")
        
        self.roster = Roster(self.raid_id, party_members, roles_str)

        return self.roster

def get_raid_by_id(raid_id: int) -> Raid:
    for raid in raids:
        if raid.raid_id == raid_id:
            return raid
    return 0

class Roster:
    def __init__(self, raid_id: int, member_ids: List[int], roles_str: str, duelist_id=0):
        self.raid = get_raid_by_id(raid_id)
        self.member_ids = member_ids.copy()
        self.roles_str = roles_str
        self.duelist = get_raider_by_id(duelist_id)
        self.party_members = []
        
        for raider_id in member_ids:
            self.party_members.append(get_raider_by_id(raider_id))

    def print_roster(self)
        for slot_id in range(len(self.party_members)):
            if (slot_id % PARTY_SIZE) == 0:
                print(self.roles_str[slot_id] + " - " + self.party_members[slot_id] + " <- PARTY LEAD\n")
            else: 
                print(self.roles_str[slot_id] + " - " + self.party_members[slot_id] +"\n")
    
    def select_duelist(self) -> Raider:
        """Chooses a duelist for DRS. Cannot be the raid host."""
        duelists = []
        
        if self.raid.raid_type == "DRS":
            for party_member in self.party_members:
                if party_member.duelist and party_member != self.raid.raid_host:
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

