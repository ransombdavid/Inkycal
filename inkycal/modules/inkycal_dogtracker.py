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
import pathlib

module_folder = pathlib.Path(__file__).parent.resolve()
filename = os.path.basename(__file__).split(".py")[0]
logger = logging.getLogger(filename)

FEEDING = "Feeding"
WALK = "Walk"
GREENIE = "Greenie"
TREAT = "Treat"


def _format_time(time_string):
    try:
        return arrow.get(time_string, "HH:mm:ss").format("hh:mm A")
    except:
        return time_string


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
        "dog_name": {"label": "Name of your dog"},
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
        self.round_temperature = config.get("greenie", False)
        self.round_windspeed = config.get("treat", False)
        self.dog_name = config.get("dog_name", "Dog")

        # additional configuration
        self.timezone = get_system_tz()
        self.db_file_path = os.path.join(os.path.join(top_level, "db"), "dogtracker.db")
        # TODO: only for windows testing on project stored in wsl. sqlite gives database locked error otherwise
        # self.db_file_path = "C:\\development\\dogtracker.db"
        self.dog_image_location = os.path.join(
            os.path.join(module_folder, "images"), "pug_dog.png"
        )
        # give an OK message
        logger.info(f"{filename} loaded")

    def init_db(self):
        if not os.path.isfile(self.db_file_path):
            logger.info(f"Creating new dogtracker db {self.db_file_path}")
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
        self._add_activity_row(FEEDING)

    def add_walk(self):
        self._add_activity_row(WALK)

    def add_treat(self):
        self._add_activity_row(TREAT)

    def add_greenie(self):
        self._add_activity_row(GREENIE)

    def get_all_todays_activities(self):
        activities = dict()
        todays_date = arrow.now(self.timezone).format("YYYY-MM-DD")
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

    def print_activity_times(
        self, base_image, activity_times, starting_position, box_size, line_height
    ):
        if len(activity_times) > 0:
            # TODO make sure you don't overflow the bottom of the module
            for pos in range(0, len(activity_times)):
                write(
                    base_image,
                    (starting_position[0], starting_position[1] + (pos * line_height)),
                    box_size,
                    _format_time(activity_times[pos]),
                    font=self.font,
                )

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
        row4 = row3 + line_gap + row_height

        line_height = 20

        # Draw lines on each row and border
        ############################################################################
        # draw = ImageDraw.Draw(im_black)
        # draw.line((0, 0, im_width, 0), fill='red')
        # draw.line((0, im_height-1, im_width, im_height-1), fill='red')
        # draw.line((0, row1, im_width, row1), fill='black')
        # draw.line((0, row1+row_height, im_width, row1+row_height), fill='black')
        # draw.line((0, row2, im_width, row2), fill='black')
        # draw.line((0, row2+row_height, im_width, row2+row_height), fill='black')
        # draw.line((0, row3, im_width, row3), fill='black')
        # draw.line((0, row3+row_height, im_width, row3+row_height), fill='black')
        ############################################################################

        # Positions for dog tracking
        label_pos = (col1, 0)
        dog_name_pos = (col1, row2)
        dog_image_pos = (col1, row3)

        meal_label_pos = (col2, row1)
        meal_time_pos = (col2, row2)

        walk_label_pos = (col3, row1)
        walk_time_pos = (col3, row2)

        greenie_label_pos = (col4, row1)
        greenie_time_pos = (col4, row2)

        # Get current time
        now = arrow.utcnow()

        logger.debug("getting daily activities")

        todays_activities = self.get_all_todays_activities()

        for key, val in todays_activities.items():
            logger.debug((key, val))

        # Fill label details in col 1

        write(
            im_black,
            label_pos,
            (col_width, row_height),
            "Daily Activity",
            font=self.font,
        )

        write(
            im_black,
            dog_name_pos,
            (col_width, row_height),
            self.dog_name,
            font=self.font,
        )

        im1 = Image.open(self.dog_image_location).convert("RGBA")
        im1 = im1.resize((row_height, row_height))
        im_black.paste(im=im1, box=dog_image_pos, mask=im1)

        write(
            im_black,
            meal_label_pos,
            (col_width, row_height),
            "Meals",
            font=self.font,
        )

        meal_times = todays_activities.get(FEEDING, [])
        self.print_activity_times(
            im_black,
            activity_times=meal_times,
            starting_position=meal_time_pos,
            box_size=(col_width, row_height),
            line_height=line_height,
        )

        write(
            im_black,
            walk_label_pos,
            (col_width, row_height),
            "Walks",
            font=self.font,
        )
        walk_times = todays_activities.get(WALK, [])
        self.print_activity_times(
            im_black,
            activity_times=walk_times,
            starting_position=walk_time_pos,
            box_size=(col_width, row_height),
            line_height=line_height,
        )

        write(
            im_black,
            greenie_label_pos,
            (col_width, row_height),
            "Greenie",
            font=self.font,
        )

        greenie_times = todays_activities.get(GREENIE, [])
        self.print_activity_times(
            im_black,
            activity_times=greenie_times,
            starting_position=greenie_time_pos,
            box_size=(col_width, row_height),
            line_height=line_height,
        )

        # draw border around module
        draw_border(
            im_black,
            (5, 5),
            (im_width - 10, im_height - 10),
            shrinkage=(0, 0),
        )

        # return the images ready for the display
        return im_black, im_colour


if __name__ == "__main__":
    print(f"running {filename} in standalone mode")
    example_config = {
        "position": 2,
        "name": "DogTracker",
        "config": {
            "size": [600, 250],
            "greenie": True,
            "treat": True,
            "dog_name": "Ripley",
            "padding_x": 10,
            "padding_y": 10,
            "fontsize": 12,
            "language": "en",
        },
    }
    dog_tracker = DogTracker(example_config)
    im_black, _ = dog_tracker.generate_image()
    im_black.save(f"C:\\development\\dog_debug_black.png", "PNG")
