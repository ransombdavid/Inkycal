#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Dog tracking module for Inky-Calendar software.
"""

from inkycal.modules.template import inkycal_module
from inkycal.custom import *

import math, decimal
import arrow
from locale import getdefaultlocale as sys_locale
import sqlite3
from contextlib import closing

filename = os.path.basename(__file__).split(".py")[0]
logger = logging.getLogger(filename)


class DogTracker(inkycal_module):
    """DogTracker class
    Tracks daily feeding/treats
    """

    name = "Dog Tracker - Tracks daily feeding/treats"

    requires = {}

    optional = {
        "greenie": {
            "label": "Add a section for tracking greenies?",
            "options": [True, False],
        },
        "treats": {
            "label": "Add a section for tracking treats?",
            "options": [True, False],
        },
        "dog_name": {
            "label": "Name of your dog"
        },
    }

    def __init__(self, config):
        """Initialize inkycal_dogtracker module"""

        super().__init__(config)

        config = config["config"]

        # Check if all required parameters are present
        for param in self.requires:
            if not param in config:
                raise Exception(f"config is missing {param}")

        # optional parameters
        self.round_temperature = config.get('greenie', False)
        self.round_windspeed = config.get('treat', False)
        self.dog_name = config.get('dog_name', "Dog")

        # additional configuration
        self.timezone = get_system_tz()
        # self.db_file_path = os.path.join(os.path.join(top_level, "db"), "dogtracker.db")
        # TODO: only for windows testing on project stored in wsl. sqlite gives database locked error otherwise
        self.db_file_path = "C:\\development\\dogtracker.db"
        # give an OK message
        print(f"{filename} loaded")

    def init_db(self):
        if not os.path.isfile(self.db_file_path):
            print(f"Creating new dogtracker db {self.db_file_path}")
            with sqlite3.connect(self.db_file_path, timeout=10) as connection:
                cursor = connection.cursor()
                # Create table
                cursor.execute(
                    "CREATE TABLE dogtracking (activity_date text, activity_time text, activity_name text)"
                )
                # Save (commit) the changes
                connection.commit()
                cursor.close()

    def _add_activity_row(self, activity_string):
        with sqlite3.connect(self.db_file_path, timeout=10) as connection:
            with closing(connection.cursor()) as cursor:
                activity_timestamp = arrow.now(self.timezone)
                # Create table
                cursor.execute(
                    f"""INSERT INTO dogtracking (activity_date, activity_time, activity_name) 
                   VALUES ('{activity_timestamp.format("YYYY-MM-DD")}', 
                           '{activity_timestamp.format("HH:mm:ss")}', 
                           '{activity_string}')"""
                )
                # Save (commit) the changes
                connection.commit()

    def add_feeding(self):
        self._add_activity_row("Feeding")

    def add_walk(self):
        self._add_activity_row("Walk")

    def add_treat(self):
        self._add_activity_row("Treat")

    def add_greenie(self):
        self._add_activity_row("Greenie")

    def get_all_todays_activities(self):
        activities = dict()
        todays_date = arrow.now(self.timezone).format('YYYY-MM-DD')
        print(f"Today's date {todays_date}")
        self.init_db()
        connection = sqlite3.connect(self.db_file_path, timeout=10)
        cursor = connection.cursor()
        cursor.execute(
            f"select activity_time, activity_name from dogtracking where activity_date='{todays_date}'"
        )
        for row in cursor.fetchall():
            if row[1] not in activities:
                activities[row[1]] = list()
            activities[row[1]].append(row[0])
        cursor.close()
        connection.close()

        # sort the activities chronologically
        for activity in activities:
            activities[activity].sort()
        return activities

    def generate_image(self):
        """Generate image for this module"""

        # Define new image size with respect to padding
        im_width = int(self.width - (2 * self.padding_left))
        im_height = int(self.height - (2 * self.padding_top))
        im_size = im_width, im_height
        logger.info(f"Image size: {im_size}")

        # Create an image for black pixels and one for coloured pixels
        im_black = Image.new("RGB", size=im_size, color="white")
        im_colour = Image.new("RGB", size=im_size, color="white")

        #   column1    column2    column3    column4
        # |----------|----------|----------|----------|
        # | Date     | Meals    | Walks    | Greenies |
        # | Dog Name |----------|----------|----------|
        # |          |          |          |          |
        # | dog icon |----------|----------|----------|
        # |          |          |          |          |
        # |----------|----------|----------|----------|

        # Calculate size rows and columns
        col_width = im_width // 4

        # Ratio width height
        image_ratio = im_width / im_height

        row_height = im_height // 3

        logger.debug(f"row_height: {row_height} | col_width: {col_width}")

        # Calculate spacings for better centering
        spacing_top = int((im_width % col_width) / 2)
        spacing_left = int((im_height % row_height) / 2)

        # Define sizes for weather icons
        icon_small = int(col_width / 3)
        icon_medium = icon_small * 2
        icon_large = icon_small * 3

        # Calculate the x-axis position of each col
        col1 = spacing_top
        col2 = col1 + col_width
        col3 = col2 + col_width
        col4 = col3 + col_width

        # Calculate the y-axis position of each row
        line_gap = int((im_height - spacing_top - 3 * row_height) // 4)

        row1 = line_gap
        row2 = row1 + line_gap + row_height
        row3 = row2 + line_gap + row_height

        # Draw lines on each row and border
        ############################################################################
        ##    draw = ImageDraw.Draw(im_black)
        ##    draw.line((0, 0, im_width, 0), fill='red')
        ##    draw.line((0, im_height-1, im_width, im_height-1), fill='red')
        ##    draw.line((0, row1, im_width, row1), fill='black')
        ##    draw.line((0, row1+row_height, im_width, row1+row_height), fill='black')
        ##    draw.line((0, row2, im_width, row2), fill='black')
        ##    draw.line((0, row2+row_height, im_width, row2+row_height), fill='black')
        ##    draw.line((0, row3, im_width, row3), fill='black')
        ##    draw.line((0, row3+row_height, im_width, row3+row_height), fill='black')
        ############################################################################

        # Positions for current weather details
        weather_icon_pos = (col1, 0)
        temperature_icon_pos = (col2, row1)
        temperature_pos = (col2 + icon_small, row1)
        humidity_icon_pos = (col2, row2)
        humidity_pos = (col2 + icon_small, row2)
        windspeed_icon_pos = (col2, row3)
        windspeed_pos = (col2 + icon_small, row3)

        # Positions for sunrise, sunset, moonphase
        moonphase_pos = (col3, row1)
        sunrise_icon_pos = (col3, row2)
        sunrise_time_pos = (col3 + icon_small, row2)
        sunset_icon_pos = (col3, row3)
        sunset_time_pos = (col3 + icon_small, row3)

        # Positions for forecast 1
        stamp_fc1 = (col4, row1)
        icon_fc1 = (col4, row1 + row_height)
        temp_fc1 = (col4, row3)

        # Get current time
        now = arrow.utcnow()

        logger.debug("getting daily activities")

        todays_activities = self.get_all_todays_activities()

        for key, val in todays_activities.items():
            logger.debug((key, val))

        # Fill label details in col 1

        write(
            im_black,
            weather_icon_pos,
            (col_width - icon_small, row_height),
            "Daily Activity",
            font=self.font,
        )

        # # Add the forecast data to the correct places
        # for pos in range(1, len(fc_data) + 1):
        #     stamp = fc_data[f"fc{pos}"]["stamp"]
        #
        #     icon = weathericons[fc_data[f"fc{pos}"]["icon"]]
        #     temp = fc_data[f"fc{pos}"]["temp"]
        #
        #     write(
        #         im_black,
        #         eval(f"stamp_fc{pos}"),
        #         (col_width, row_height),
        #         stamp,
        #         font=self.font,
        #     )
        #     draw_icon(
        #         im_colour,
        #         eval(f"icon_fc{pos}"),
        #         (col_width, row_height + line_gap * 2),
        #         icon,
        #     )
        #     write(
        #         im_black,
        #         eval(f"temp_fc{pos}"),
        #         (col_width, row_height),
        #         temp,
        #         font=self.font,
        #     )

        border_h = row3 + row_height
        border_w = col_width - 3  # leave 3 pixels gap

        # Add borders around each sub-section
        draw_border(
            im_black, (col1, row1), (col_width * 3 - 3, border_h), shrinkage=(0, 0)
        )

        # for _ in range(4, 8):
        #     draw_border(
        #         im_black,
        #         (eval(f"col{_}"), row1),
        #         (border_w, border_h),
        #         shrinkage=(0, 0),
        #     )

        # return the images ready for the display
        return im_black, im_colour


if __name__ == "__main__":
    print(f"running {filename} in standalone mode")
