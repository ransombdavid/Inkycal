import arrow
import logging
import os
import sqlite3
from contextlib import closing

from inkycal.custom import get_system_tz, top_level

FEEDING = "Feeding"
WALK = "Walk"
GREENIE = "Greenie"
TREAT = "Treat"


def default_dogtracker_db_path():
    # TODO: only for windows testing on project stored in wsl. sqlite gives database locked error otherwise
    # return "C:\\development\\dogtracker.db"
    return os.path.join(os.path.join(top_level, "db"), "dogtracker.db")


def init_db(db_file_path):
    if not os.path.isfile(db_file_path):
        logging.info(f"Creating new dogtracker db {db_file_path}")
        with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
            cursor = connection.cursor()
            # Create table
            cursor.execute(
                "CREATE TABLE dogtracking (activity_date text, activity_time text, activity_name text)"
            )
            # Save (commit) the changes
            connection.commit()
            cursor.close()


def _add_activity_row(db_file_path, activity_string):
    init_db(db_file_path)
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            timezone = get_system_tz()
            activity_timestamp = arrow.now(timezone)
            # Create table
            cursor.execute(
                f"""INSERT INTO dogtracking (activity_date, activity_time, activity_name) 
               VALUES ('{activity_timestamp.format("YYYY-MM-DD")}', 
                       '{activity_timestamp.format("HH:mm:ss")}', 
                       '{activity_string}')"""
            )
            # Save (commit) the changes
            connection.commit()


def add_feeding(db_file_path):
    _add_activity_row(db_file_path, FEEDING)


def add_walk(db_file_path):
    _add_activity_row(db_file_path, WALK)


def add_treat(db_file_path):
    _add_activity_row(db_file_path, TREAT)


def add_greenie(db_file_path):
    _add_activity_row(db_file_path, GREENIE)


def get_all_todays_activities(db_file_path):
    activities = dict()
    timezone = get_system_tz()
    todays_date = arrow.now(timezone).format("YYYY-MM-DD")
    init_db(db_file_path)

    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                f"select activity_time, activity_name from dogtracking where activity_date='{todays_date}'"
            )
            for row in cursor.fetchall():
                if row[1] not in activities:
                    activities[row[1]] = list()
                activities[row[1]].append(row[0])

    # sort the activities chronologically
    for activity in activities:
        activities[activity].sort()
    return activities
