from time import sleep

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

# TODO: only for windows testing on project stored in wsl. sqlite gives database locked error otherwise
# DEFAULT_DOGTRACKER_DB_PATH = "C:\\development\\dogtracker.db"
DEFAULT_DOGTRACKER_DB_PATH = os.path.join(
    os.path.join(top_level, "db"), "dogtracker.db"
)


def init_db(db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH):
    logging.info(f"dogtracker_utils.init_db: {db_file_path}")
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


def _add_activity_row(
    activity_string,
    db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH,
    max_activities_per_minute=1,
):
    init_db(db_file_path)
    result = 0
    with closing(sqlite3.connect(db_file_path, timeout=10)) as connection:
        with closing(connection.cursor()) as cursor:
            timezone = get_system_tz()
            activity_timestamp = arrow.now(timezone)
            activity_date = activity_timestamp.format("YYYY-MM-DD")
            activity_time = activity_timestamp.format("HH:mm:ss")
            should_insert_new_row = True

            # limit number of activities stored in the same minute (to help with rate limiting)
            if max_activities_per_minute > 0:
                cursor.execute(
                    f"""select count(*) from dogtracking 
                        where activity_date='{activity_date}' 
                          and substr(activity_time, 1, 5) = '{activity_time[:5]}'
                    """
                )
                row_count = cursor.fetchone()
                if row_count is not None and row_count[0] >= max_activities_per_minute:
                    logging.debug(
                        "Already found too many rows for this activity in this minute"
                    )
                    should_insert_new_row = False

            if should_insert_new_row:
                cursor.execute(
                    f"""INSERT INTO dogtracking (activity_date, activity_time, activity_name) 
                   VALUES ('{activity_date}', 
                           '{activity_time}', 
                           '{activity_string}')"""
                )
                result = 1
            else:
                result = -1

            # Save (commit) the changes
            connection.commit()
    return result


def add_feeding(db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH):
    return _add_activity_row(FEEDING, db_file_path)


def add_walk(db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH):
    return _add_activity_row(WALK, db_file_path)


def add_treat(db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH):
    return _add_activity_row(TREAT, db_file_path)


def add_greenie(db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH):
    return _add_activity_row(GREENIE, db_file_path)


def get_all_todays_activities(db_file_path: str = DEFAULT_DOGTRACKER_DB_PATH):
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
