import logging
import os
import traceback
from logging.handlers import RotatingFileHandler
from time import sleep

import arrow
import keyboard

from inkycal.modules.modules_utilities.dogtracker_utils import (
    add_feeding,
    add_walk,
    add_greenie,
    # add_treat,
)
from inkycal.custom import get_system_tz, top_level
from inkycal.custom.sqlite_utils import (
    start_inkycal,
    stop_inkycal,
    should_inkycal_stop,
    should_inkycal_refresh,
    add_refresh,
    get_inkycal_settings_file,
)
from inkycal.main import Inkycal
from PIL import Image


stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)

on_rtd = os.environ.get("READTHEDOCS") == "True"
if on_rtd:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s |  %(levelname)s: %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        handlers=[stream_handler],
    )

else:
    # Save all logs to a file, which contains more detailed output
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s |  %(levelname)s: %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
        handlers=[
            stream_handler,  # add stream handler from above
            RotatingFileHandler(  # log to a file too
                f"{top_level}/logs/inkycal.log",  # file to log
                maxBytes=2097152,  # 2MB max filesize
                backupCount=5,  # create max 5 log files
            ),
        ],
    )

filename = os.path.basename(__file__).split(".py")[0]
logger = logging.getLogger(filename)


class InkyCalWrapper:
    def __init__(
        self,
        settings_path="/boot/settings.json",
        render=True,
        optimize=True,
        accept_keypress=True,
    ):
        self.render = render
        self.optimize = optimize
        self.settings_path = settings_path
        self.accept_keypress = accept_keypress

        self.inky = self.build_inkycal()

    def build_inkycal(self):
        return Inkycal(
            settings_path=self.settings_path, render=self.render, optimize=self.optimize
        )

    def run(self):
        # Variable to keep the main loop running
        running = True
        start_inkycal()
        add_refresh(arrow.now(get_system_tz()))

        def handle_keypress(key):
            hotkey_pressed = False
            if key.name == "esc":
                stop_inkycal()
            elif key.name == "1":
                result = add_feeding()
                if result > 0:
                    hotkey_pressed = True
            elif key.name == "2":
                result = add_walk()
                if result > 0:
                    hotkey_pressed = True
            elif key.name == "3":
                result = add_greenie()
                if result > 0:
                    hotkey_pressed = True
            elif key.name == "4":
                # refresh screen
                hotkey_pressed = True

            if hotkey_pressed:
                sleep(2)
                add_refresh(arrow.now(get_system_tz()))

        if self.accept_keypress:
            keyboard.on_press(handle_keypress)

        # Main loop
        while running:
            loop_start = arrow.now(tz=get_system_tz())
            running = not should_inkycal_stop()
            if not running:
                logger.info("Found stop state in db")
                print("Found stop state in db")
                break

            refresh_screen = should_inkycal_refresh()

            if refresh_screen:
                logger.info("Refreshing the screen")
                self._show_refresh_image()

                # check for updated settings file
                settings_file = get_inkycal_settings_file()
                if settings_file != self.settings_path:
                    logger.info(f"New settings file found: {settings_file}")
                    self.settings_path = settings_file
                    self.inky = self.build_inkycal()

                self.inky.run_once()
                self._add_refresh_icon()  # cache refresh image
                seconds_before_next_update = self.inky.countdown()
                time_to_next_refresh = loop_start.shift(
                    seconds=seconds_before_next_update
                )
                add_refresh(time_to_next_refresh)
                logger.info(f"Time to next refresh: {time_to_next_refresh.format()}")

            sleep(2)

    def _show_refresh_image(self):
        refresh_image = Image.open(f"{self.inky.image_folder}/refresh.png")
        self.inky.Display.render(refresh_image)

    def _add_refresh_icon(self):
        background_image = self.inky._merge_bands()

        # make a copy of the dashboard image in the flask server
        background_image.save(
            f"{top_level}/server/app/static/images/dashboard.png", "PNG"
        )

        # add refresh icon to center
        refresh_image = Image.open(f"{self.inky.image_folder}/refresh_icon.png")
        background_size = background_image.size
        min_side = int(min(background_size) / 2)
        refresh_image = refresh_image.resize((min_side, min_side), Image.ANTIALIAS)

        center_coord = (
            round(background_size[0] / 2 - min_side / 2),
            round(background_size[1] / 2 - min_side / 2),
        )
        background_image.paste(refresh_image, center_coord)
        background_image.save(f"{self.inky.image_folder}/refresh.png", "PNG")


if __name__ == "main":
    print("Running InkyCalWrapper in standalone mode")
    try:
        inky_game = InkyCalWrapper(
            "C:\\development\\settings.json",
            render=True,
            optimize=False,
            accept_keypress=False,
        )
        inky_game.run()
    except:
        print(traceback.format_exc())
