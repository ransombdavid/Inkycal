import arrow
import logging
import os
import sqlite3
from contextlib import closing

from inkycal.custom import get_system_tz, top_level

RUNNING = "RUNNING"
WALK = "Walk"
GREENIE = "Greenie"
TREAT = "Treat"


def default_inkycal_db_path():
    # TODO: only for windows testing on project stored in wsl. sqlite gives database locked error otherwise
    # return "C:\\development\\inkycal.db"
    return os.path.join(os.path.join(top_level, "db"), "inkycal.db")


def init_db(db_file_path):
    if not os.path.isfile(db_file_path):
        logging.info(f"Creating new inkycal db {db_file_path}")
        with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
            cursor = connection.cursor()
            # Create table
            cursor.execute(
                "CREATE TABLE inkycal (activity_date text, activity_time text, activity_name text)"
            )
            cursor.execute("CREATE UNIQUE INDEX idx_inkycal_name ON inkycal (activity_name);")
            # Save (commit) the changes
            connection.commit()
            cursor.close()


def _add_activity_row(db_file_path, activity_string, activity_timestamp):
    init_db(db_file_path)
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            # Create table
            cursor.execute(
                f"""INSERT OR REPLACE INTO inkycal (activity_date, activity_time, activity_name) 
               VALUES ('{activity_timestamp.format("YYYY-MM-DD") if activity_timestamp else 'null'}', 
                       '{activity_timestamp.format("HH:mm:ss") if activity_timestamp else 'null'}', 
                       '{activity_string}')"""
            )
            # Save (commit) the changes
            connection.commit()


def stop_inkycal(db_file_path):
    _add_activity_row(db_file_path, RUNNING, None)


def start_inkycal(db_file_path):
    timezone = get_system_tz()
    activity_timestamp = arrow.now(timezone)
    _add_activity_row(db_file_path, RUNNING, activity_timestamp)

def add_refresh(db_file_path):
    