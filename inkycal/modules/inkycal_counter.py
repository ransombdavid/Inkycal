#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Pill Tracker module for Inky-Calendar software.
"""
from inkycal.modules.modules_utilities.counter_utils import get_counts
from inkycal.modules.template import inkycal_module
from inkycal.custom import *

import arrow
import pathlib

module_folder = pathlib.Path(__file__).parent.resolve()
filename = os.path.basename(__file__).split(".py")[0]
logger = logging.getLogger(filename)


def _format_time(time_string):
    try:
        return arrow.get(time_string, "HH:mm:ss").format("hh:mm A")
    except:
        return time_string


class PillCounter(inkycal_module):
    """PillCounter class
    Tracks pill counts
    """

    name = "Pill Counter - Tracks pill counts"

    requires = {
        "credentials_file": {
            "label": "Location of the google api credentials json file"
        },
        "track_d": {"label": "Track dilaudid count", "default": False},
    }

    optional = {}

    def __init__(self, config):
        """Initialize inkycal_counter module"""

        super().__init__(config)

        config = config["config"]

        # Check if all required parameters are present
        for param in self.requires:
            if param not in config:
                raise Exception(f"config is missing {param}")

        # additional configuration
        self._db_file_path = None
        self.timezone = get_system_tz()
        self.credentials_file = config["credentials_file"]
        self.track_d = config.get("track_d", False)

        # give an OK message
        logger.info(f"{filename} loaded")

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

        #   column1    column2
        # |----------|----------|
        # | P Count  | D Count  |
        # |----------|----------|
        # | Days left label     |
        # |----------|----------|

        # Calculate size rows and columns
        col_width = im_width // 2

        # Ratio width height
        image_ratio = im_width / im_height

        row_height = im_height // 2

        logger.debug(f"row_height: {row_height} | col_width: {col_width}")

        # Calculate spacings for better centering
        spacing_top = int((im_width % col_width) / 2)
        spacing_left = int((im_height % row_height) / 2)

        # Calculate the x-axis position of each col
        col1 = spacing_top
        col2 = col1 + col_width

        # Calculate the y-axis position of each row
        line_gap = int((im_height - spacing_top - 3 * row_height) // 4)

        row1 = line_gap
        row2 = row1 + line_gap + row_height

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

        # Positions for counts
        p_count_pos = (col1, 0)
        if self.track_d:
            d_count_pos = (col2, 0)
            days_left_pos = (col1, row2)
        else:
            d_count_pos = None
            days_left_pos = (col2, 0)

        # Get current time
        now = arrow.now(self.timezone)

        # if it's before 8AM, use yesterday's date so the count is closer to accurate
        # in case erin is up late
        if now.hour <= 8:
            now = now.shift(days=-1)

        date_string = now.format("MM/DD/YY")

        logger.debug("getting pill count")

        todays_counts = get_counts(
            date_string=date_string, credentials_file=self.credentials_file
        )

        if todays_counts is None:
            logger.error("Error retrieving counts")
            write(
                im_black,
                p_count_pos,
                (col_width, row_height),
                "Error retrieving counts",
                font=self.font,
            )
            return im_black, im_colour

        logger.debug(todays_counts)

        pill_count_format = "{:.1f}"
        p_text = pill_count_format.format(todays_counts.p_count) + " P"
        d_text = pill_count_format.format(todays_counts.d_count) + " D"
        days_text = str(todays_counts.days_left) + " days left"

        if self.track_d:
            write(
                im_black,
                p_count_pos,
                (col_width, row_height),
                p_text,
                font=self.font,
            )

            write(
                im_black,
                d_count_pos,
                (col_width, row_height),
                d_text,
                font=self.font,
            )

            write(
                im_black,
                days_left_pos,
                (im_width, row_height),
                days_text,
                font=self.font,
            )
        else:
            line_text = p_text + "   " + days_text
            write(
                im_black,
                p_count_pos,
                (im_width, im_height),
                line_text,
                font=self.font,
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
        "position": 3,
        "name": "PillCounter",
        "config": {
            "size": [800, 250],
            "prescription_days": 28,
            "credentials_file": "C:\\development\\credentials.json",
            "track_d": False,
            "padding_x": 10,
            "padding_y": 10,
            "fontsize": 45,
            "language": "en",
        },
    }
    pill_counter = PillCounter(example_config)
    im_black, _ = pill_counter.generate_image()
    im_black.save(f"C:\\development\\count_debug_black.png", "PNG")
