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

TIMESTAMP_FORMAT = "YYYY-MM-DD[T]HH:mm:ss"


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
                "CREATE TABLE inkycal (activity_name text, activity_state text, activity_time text)"
            )
            cursor.execute(
                "CREATE UNIQUE INDEX idx_inkycal_name ON inkycal (activity_name);"
            )
            # Save (commit) the changes
            connection.commit()
            cursor.close()


def _add_activity_row(db_file_path, activity_string, activity_state):
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


def stop_inkycal(db_file_path):
    _add_activity_row(db_file_path, RUNNING, STOP)


def start_inkycal(db_file_path):
    _add_activity_row(db_file_path, RUNNING, START)


def should_inkycal_stop(db_file_path):
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


def add_refresh(db_file_path, refresh_time):
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


def should_inkycal_refresh(db_file_path):
    init_db(db_file_path)

    timezone = get_system_tz()
    now_time = arrow.now(timezone)
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
                # print("Found refresh time: " + results_time.format())
                if results_time < now_time:
                    print(
                        f"refresh time is in the past {results_time.format()} < {now_time.format()}"
                    )
                    return True
    return False
