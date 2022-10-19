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
            preferred_role TEXT DEFAULT 'd',
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


def get_raiders_by_raid_id(raid_id: int) -> List[int]:
    """Returns raider_id for each raider participating in the raid."""
    participants = []
    
    # TODO learn postgres
    return participants
