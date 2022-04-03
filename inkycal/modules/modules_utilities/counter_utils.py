from __future__ import print_function

import datetime
import logging
import os.path
from dataclasses import dataclass
from typing import Optional

from inkycal.custom.functions import top_level

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID the counter spreadsheet.
SPREADSHEET_ID = "1EmnY_1I7yfQchuPBz3MUYTQ-3ZvP4AGg81h2Dzlbt9g"

P_ROW = 3
D_ROW = 7
REMAINING_ROW = 6


@dataclass
class CounterData:
    p_count: float
    d_count: float
    days_left: int
    start_date: datetime.date


def get_counts(
    date_string: str, credentials_file: str = "/boot/credentials.json"
) -> Optional[CounterData]:
    # add credentials to the account
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, SCOPES)

    # authorize the clientsheet
    client = gspread.authorize(creds)

    # get the instance of the Spreadsheet
    sheet = client.open_by_key(SPREADSHEET_ID)

    # get the first sheet of the Spreadsheet
    sheet_instance = sheet.get_worksheet(0)

    start_date = datetime.datetime.strptime(
        sheet_instance.acell("B2").value, "%m/%d/%y"
    ).date()
    date_list = sheet_instance.row_values(2)
    current_date_col = date_list.index(date_string)
    # can't find current date, might need to update spreadsheet
    if current_date_col < 0:
        logging.error(f"Could not find current date '{date_string}'")
        return None
    else:
        # gspread is index 1 based
        current_date_col += 1

    current_p_count = float(sheet_instance.cell(row=P_ROW, col=current_date_col).value)
    current_d_count = float(sheet_instance.cell(row=D_ROW, col=current_date_col).value)
    days_remaining = int(
        sheet_instance.cell(row=REMAINING_ROW, col=current_date_col).value
    )

    return CounterData(
        p_count=current_p_count,
        d_count=current_d_count,
        days_left=days_remaining,
        start_date=start_date,
    )


if __name__ == "__main__":
    CREDENTIALS_FILE = os.path.join(os.path.join(top_level, "db"), "credentials.json")
    counter_data = get_counts("04/03/22", CREDENTIALS_FILE)
    print(counter_data)
