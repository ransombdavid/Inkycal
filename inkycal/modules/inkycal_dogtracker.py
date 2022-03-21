#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Dog tracking module for Inky-Calendar software.
"""
from inkycal.modules.modules_utilities.dogtracker_utils import (
    default_dogtracker_db_path,
    get_all_todays_activities,
    FEEDING,
    WALK,
    GREENIE,
    TREAT
)
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
            if param not in config:
                raise Exception(f"config is missing {param}")

        # optional parameters
        self.round_temperature = config.get("greenie", False)
        self.round_windspeed = config.get("treat", False)
        self.dog_name = config.get("dog_name", "Dog")

        # additional configuration
        self._db_file_path = None
        self.timezone = get_system_tz()
        self.dog_image_location = os.path.join(
            os.path.join(module_folder, "images"), "pug_dog.png"
        )
        # give an OK message
        logger.info(f"{filename} loaded")

    @property
    def db_file_path(self):
        if not self._db_file_path:
            self._db_file_path = default_dogtracker_db_path()
        return self._db_file_path

    def _print_activity_times(
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

        todays_activities = get_all_todays_activities(self.db_file_path)

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
        self._print_activity_times(
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
        self._print_activity_times(
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
        self._print_activity_times(
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
