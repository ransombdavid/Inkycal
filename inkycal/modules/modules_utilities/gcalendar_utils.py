from __future__ import annotations

import logging
import os.path
import re
from dataclasses import dataclass
from typing import Optional, List

import datetime

import arrow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from inkycal.custom.functions import top_level

from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


@dataclass
class EventData:
    summary: str
    start_time: arrow.Arrow
    end_time: arrow.Arrow
    creator: str
    is_all_day: bool = False


def get_events(
    calendar_id: str,
    start_time: arrow.Arrow,
    max_days: int = 60,
    credentials_file: str = "/boot/credentials.json",
) -> Optional[List[EventData]]:
    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, SCOPES)
    apartment_events = []
    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = start_time.isoformat()
        end = start_time.shift(days=+max_days).isoformat()
        logging.info(f"Getting the events from the next {max_days} days")
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                timeMax=end,
                # maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            logging.info("No upcoming events found.")
            return apartment_events

        # Prints the start and name of the next 10 events
        date_only_pattern = re.compile("^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
        for event in events:
            raw_start = event["start"].get("dateTime", event["start"].get("date"))
            raw_end = event["end"].get("dateTime", event["end"].get("date"))
            is_all_day = False
            if date_only_pattern.match(raw_start):
                is_all_day = True
                start = arrow.get(raw_start, "YYYY-MM-DD").replace(tzinfo="local")
                end = arrow.get(raw_end, "YYYY-MM-DD").replace(tzinfo="local")
            else:
                start = arrow.get(raw_start)
                end = arrow.get(raw_end)

            summary = event["summary"]
            creator = event["creator"]["email"]
            apartment_events.append(EventData(summary, start, end, creator, is_all_day))

    except HttpError as error:
        logging.error("An error occurred: %s" % error)

    return apartment_events


def filter_events(
    events: List[EventData], start_time: arrow.Arrow, end_time: arrow.Arrow
):
    return [
        event
        for event in events
        if event.start_time >= start_time and event.end_time <= end_time
    ]


if __name__ == "__main__":
    CREDENTIALS_FILE = os.path.join(os.path.join(top_level, "db"), "credentials.json")
    counter_data = get_events(
        "holland.ln.apartment@gmail.com",
        arrow.utcnow(),
        credentials_file=CREDENTIALS_FILE,
    )
    print(counter_data)
