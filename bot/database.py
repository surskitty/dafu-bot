from typing import List
import psycopg2
from psycopg2 import Error

def create_connection():
    try:
        conn = psycopg2.connect(database=PGDATABASE, user=PGUSER, password=PGPASSWORD, host=PGHOST,port=PGPORT)
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)    
    return conn

def initialize_db_with_tables(conn):
    """initialise database"""
    conn = create_connection()
    create_tables(conn)
    commands = (
        """
        CREATE TABLE IF NOT EXISTS raiders (
            raider_id SERIAL PRIMARY KEY,
            discord_id INTEGER NOT NULL UNIQUE,
            character_name TEXT NOT NULL UNIQUE,
            roles TEXT DEFAULT 'd',
            preferred_role CHAR DEFAULT 'd',
            notoriety INTEGER DEFAULT 0,
            party_lead BOOLEAN DEFAULT FALSE,
            reserve BOOLEAN DEFAULT FALSE,
            duelist BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS raids (
            raid_id SERIAL PRIMARY KEY,
            raid_type TEXT NOT NULL,
            host_id INTEGER NOT NULL,
            organiser_id INTEGER,
            raid_time TIMESTAMP NOT NULL,
            message_link TEXT NOT NULL UNIQUE,
            state BOOLEAN,
            FOREIGN KEY (host_id)
                REFERENCES raiders(raider_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS signups (
            raid_id INTEGER NOT NULL,
            raider_id INTEGER INTEGER NOT NULL,
            PRIMARY KEY (raid_id, grade_id)
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
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn is not None:
            conn.close()

def create_raider(conn, discord_id: int, character_name: str, roles: str, preferred_role='d')
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

def get_raider_id_by_discord_id(conn, discord_id: int):
    cur = conn.cursor()
    cur.execute("SELECT raider_id FROM raids WHERE discord_id=%s", (discord_id,))
    return cur.fetchone()[0]

def get_raid_by_id(conn, raid_id: int):
    """Find the raid given id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raids WHERE raid_id=%s", (raid_id,))
    return cur.fetchall()

def get_raider_by_id(conn, raider_id: int):
    """Find the player given id"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM raiders WHERE raider_id=%s", (raider_id,))
    return cur.fetchall()

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

def get_upcoming_raids(conn):
    """Finds the raids that have not happened yet."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT * from raids WHERE raid_time >= now();")
    except (Exception, Error) as error:
        print("Error getting upcoming raids.", error)
    return cur.fetchall()
