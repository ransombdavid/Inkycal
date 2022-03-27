import logging
import os
import traceback
from logging.handlers import RotatingFileHandler
from time import sleep

import arrow
import keyboard

import inkycal.modules
from inkycal.modules.modules_utilities.dogtracker_utils import (
    add_feeding,
    add_walk,
    add_greenie,
    add_treat,
    default_dogtracker_db_path,
)
from inkycal.custom import get_system_tz, top_level
from inkycal.custom.sqlite_utils import (
    start_inkycal,
    stop_inkycal,
    should_inkycal_stop,
    should_inkycal_refresh,
    add_refresh,
    default_inkycal_db_path,
)
from inkycal.main import Inkycal


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
    def __init__(self, settings_path="/boot/settings.json", render=True, optimize=True):
        self.inky = Inkycal(
            settings_path=settings_path, render=render, optimize=optimize
        )
        self.dog_tracker_module_index = -1
        self.dog_tracker_db = None
        for ix, module in enumerate(self.inky.modules):
            logger.info(f"Module {ix}: {module.name}")
            if type(module) is inkycal.modules.DogTracker:
                self.dog_tracker_db = module.db_file_path
                self.dog_tracker_module_index = ix
                break

    def run(self):
        # Variable to keep the main loop running
        running = True
        start_inkycal(default_inkycal_db_path())
        add_refresh(default_inkycal_db_path(), arrow.now(get_system_tz()))

        def handle_keypress(key):
            hotkey_pressed = False
            if key.name == "esc":
                stop_inkycal(default_inkycal_db_path())
            elif key.name == "1":
                result = add_feeding(default_dogtracker_db_path())
                if result > 0:
                    hotkey_pressed = True
            elif key.name == "2":
                result = add_walk(default_dogtracker_db_path())
                if result > 0:
                    hotkey_pressed = True
            elif key.name == "3":
                result = add_greenie(default_dogtracker_db_path())
                if result > 0:
                    hotkey_pressed = True

            if hotkey_pressed:
                sleep(2)
                add_refresh(default_inkycal_db_path(), arrow.now(get_system_tz()))

        keyboard.on_press(handle_keypress)

        # Main loop
        while running:
            loop_start = arrow.now(tz=get_system_tz())
            running = not should_inkycal_stop(default_inkycal_db_path())
            if not running:
                logger.info("Found stop state in db")
                print("Found stop state in db")
                break

            refresh_screen = should_inkycal_refresh(default_inkycal_db_path())

            if refresh_screen:
                logger.info("Refreshing the screen")
                self.inky.run_once()
                seconds_before_next_update = self.inky.countdown()
                time_to_next_refresh = loop_start.shift(
                    seconds=seconds_before_next_update
                )
                add_refresh(default_inkycal_db_path(), time_to_next_refresh)
                logger.info(f"Time to next refresh: {time_to_next_refresh.format()}")

            sleep(2)


if __name__ == "main":
    print("Running InkyCalWrapper in standalone mode")
    try:
        inky_game = InkyCalWrapper(
            "C:\\development\\settings.json", render=True, optimize=False
        )
        inky_game.run()
    except:
        print(traceback.format_exc())
