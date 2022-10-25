from typing import List
import psycopg2
from psycopg2 import Error
import os
from urllib.parse import urlparse 

RAIDERS_COLUMNS = ["raider_id", "discord_id", "character_name", "roles", 
                 "preferred_role", "notoriety", "party_lead", "reserve", "duelist"]

RAIDS_COLUMNS   = ["raid_id", "raid_type", "host_id", "organiser_id", 
                   "raid_time", "message_link", "state"]

RAID_TYPES = {"BA": 0, "DRN": 1, "DRS: 2"}

def create_connection():
    result = urlparse(os.getenv('DATABASE_URL'))
    USER = result.username
    PASSWORD = result.password
    DATABASE = result.path[1:]
    HOST = result.hostname
    POST = result.port

    try:
        conn = psycopg2.connect(database=DATABASE, user=USER, password=PASSWORD, host=HOST,port=PORT)
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)    
    return conn

def initialize_db_with_tables():
    """initialise database"""
    conn = create_connection()
    success = True
    commands = (
        """
        CREATE TABLE IF NOT EXISTS raiders (
            raider_id SERIAL PRIMARY KEY,
            discord_id INTEGER NOT NULL UNIQUE,
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
            host_discord INTEGER NOT NULL,
            organiser_id INTEGER,
            raid_time TIMESTAMP NOT NULL,
            message_link TEXT NOT NULL UNIQUE,
            state SMALLINT NOT NULL,
            FOREIGN KEY (host_id)
                REFERENCES raiders(raider_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS signups (
            raid_id INTEGER NOT NULL,
            raider_id INTEGER NOT NULL,
            benched BOOLEAN DEFAULT FALSE
            PRIMARY KEY (raid_id, raider_id)
            FOREIGN KEY (raid_id)
                REFERENCES raids (raid_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (raider_id)
                REFERENCES raiders (raider_id)
                ON UPDATE CASCADE ON DELETE CASCADE
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
        preferred_role = preferred_role[0]
        cur.execute(
            "INSERT INTO raiders (discord_id, character_name, roles, preferred_role) VALUES (%s, %s, %s, %s)",
            (discord_id, character_name, roles, preferred_role))
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if cur is not None:
            cur.close()

def get_raid_by_id(conn, raid_id: int):
    """Find the raid given id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raids WHERE raid_id=%s", (raid_id,))
    return cur.fetchone()

def get_raids_by_host_id(conn, host_id: int):
    """Find the raid given id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raids WHERE host_id=%s", (host_id,))
    return cur.fetchall()

def get_raider_by_id(conn, raider_id: int):
    """Find the player given id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raiders WHERE raider_id=%s", (raider_id,))
    return cur.fetchone()

def get_raider_id_by_discord_id(conn, discord_id: int):
    cur = conn.cursor()
    cur.execute("SELECT raider_id FROM raids WHERE discord_id=%s", (discord_id,))
    return cur.fetchone()[0]

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
        sql = ''' UPDATE raiders
                  SET %s = %s
                  WHERE id = %s'''
        cur = conn.cursor()
        cur.execute(sql, (field, value, raider_id))
        conn.commit()
    else:
        print(f"{field} not in raiders columns")
    if cur is not None:
        cur.close()

def update_raid(conn, field, value, raid_id):
    if field in RAIDERS_COLUMNS:
        sql = ''' UPDATE raids
                  SET %s = %s
                  WHERE id = %s'''
        cur = conn.cursor()
        cur.execute(sql, (field, value, raid_id))
        conn.commit()
    else:
        print(f"{field} not in raids columns")
    if cur is not None:
        cur.close()

def get_upcoming_raids(conn):
    """Finds the raids that have not happened yet."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT * from raids WHERE raid_time >= now();")
    except (Exception, Error) as error:
        print("Error getting upcoming raids.", error)
    return cur.fetchall()
