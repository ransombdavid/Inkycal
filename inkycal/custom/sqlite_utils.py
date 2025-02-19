import arrow
import logging
import os
import sqlite3
from contextlib import closing

from inkycal.custom import get_system_tz, top_level

RUNNING = "RUNNING"
REFRESH = "REFRESH"
STOP = "STOP"
START = "START"
SETTINGS_FILE = "SETTINGS"

TIMESTAMP_FORMAT = "YYYY-MM-DD[T]HH:mm:ss"

DEFAULT_SETTINGS_PATH = "/boot/settings.json"

# TODO: only for windows testing on project stored in wsl. sqlite gives database locked error otherwise
# DEFAULT_INKYCAL_DB_PATH = "C:\\development\\inkycal.db"
DEFAULT_INKYCAL_DB_PATH = os.path.join(os.path.join(top_level, "db"), "inkycal.db")


def init_db(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    if not os.path.isfile(db_file_path):
        logging.info(f"Creating new inkycal db {db_file_path}")
        with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
            cursor = connection.cursor()
            # Create table
            cursor.execute(
                "CREATE TABLE inkycal (activity_name text, activity_state text, activity_time text)"
            )
            cursor.execute(
                "CREATE UNIQUE INDEX idx_inkycal_name ON inkycal (activity_name);"
            )
            # Save (commit) the changes
            connection.commit()
            cursor.close()


def _add_activity_row(
    activity_string: str,
    activity_state: str,
    db_file_path: str = DEFAULT_INKYCAL_DB_PATH,
):
    init_db(db_file_path)

    timezone = get_system_tz()
    activity_timestamp = arrow.now(timezone)
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            # Create table
            cursor.execute(
                f"""INSERT OR REPLACE INTO inkycal (activity_name, activity_state, activity_time) 
               VALUES ('{activity_string}',
                       '{activity_state}',
                       '{activity_timestamp.format(TIMESTAMP_FORMAT)}')"""
            )
            # Save (commit) the changes
            connection.commit()


def stop_inkycal(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    _add_activity_row(RUNNING, STOP, db_file_path)


def start_inkycal(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    _add_activity_row(RUNNING, START, db_file_path)


def should_inkycal_stop(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    init_db(db_file_path)
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""SELECT activity_state FROM inkycal 
                    WHERE activity_name = '{RUNNING}'"""
            )
            results = cursor.fetchall()
            if results and results[0] and results[0][0] == START:
                return False
    return True


def add_refresh(refresh_time, db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    init_db(db_file_path)

    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            # Create table
            cursor.execute(
                f"""INSERT OR REPLACE INTO inkycal (activity_name, activity_state, activity_time) 
               VALUES ('{REFRESH}',
                       '',
                       '{refresh_time.format(TIMESTAMP_FORMAT)}')"""
            )
            # Save (commit) the changes
            connection.commit()


def get_next_inkycal_refresh(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    init_db(db_file_path)
    timezone = get_system_tz()
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""SELECT activity_time FROM inkycal 
                    WHERE activity_name = '{REFRESH}'"""
            )
            results = cursor.fetchall()
            # if the timestamp is in the past, return True
            if results and results[0] and results[0][0]:
                results_time = arrow.get(
                    results[0][0], TIMESTAMP_FORMAT, tzinfo=timezone
                )
                return results_time
    return None


def should_inkycal_refresh(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    init_db(db_file_path)

    timezone = get_system_tz()
    now_time = arrow.now(timezone)
    refresh_time = get_next_inkycal_refresh(db_file_path)
    # print("Found refresh time: " + results_time.format())
    if refresh_time and refresh_time < now_time:
        print(
            f"refresh time is in the past {refresh_time.format()} < {now_time.format()}"
        )
        return True
    return False


def get_inkycal_settings_file(db_file_path: str = DEFAULT_INKYCAL_DB_PATH):
    init_db(db_file_path)
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"""SELECT activity_state FROM inkycal 
                    WHERE activity_name = '{SETTINGS_FILE}'"""
            )
            results = cursor.fetchall()
            # if the timestamp is in the past, return True
            if results and results[0] and results[0][0]:
                return str(results[0][0])

    # if there is not a row for settings file, make a new one
    set_inkycal_settings_file(DEFAULT_SETTINGS_PATH, db_file_path)
    return DEFAULT_SETTINGS_PATH


def set_inkycal_settings_file(
    settings_file_location: str = "/boot/settings.json",
    db_file_path: str = DEFAULT_INKYCAL_DB_PATH,
):
    _add_activity_row(SETTINGS_FILE, settings_file_location, db_file_path)
