import logging
import os
from logging.handlers import RotatingFileHandler
from time import sleep

import arrow
import pygame

from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

import inkycal.modules
from inkycal.modules.modules_utilities.dogtracker_utils import add_feeding, add_walk, add_greenie, add_treat, default_dogtracker_db_path
from inkycal.custom import get_system_tz, top_level
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


def handle_keypress(key):
    if key.name == "esc":
        raise Exception("Exit")
    elif key.name == "1":
        add_feeding(default_dogtracker_db_path())
    elif key.name == "2":
        add_walk(default_dogtracker_db_path())
    elif key.name == "3":
        add_greenie(default_dogtracker_db_path())

    print(key.name)


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
        next_available_key_action = None
        refresh_screen = False

        # Get the time of initial run
        runtime = arrow.now()
        time_to_next_refresh = None
        # Main loop
        while running:
            loop_start = arrow.now(tz=get_system_tz())
            if not time_to_next_refresh or time_to_next_refresh < loop_start:
                logger.info(
                    "Haven't refreshed yet"
                    if not time_to_next_refresh
                    else "Time to refresh now"
                )
                refresh_screen = True
                time_to_next_refresh = loop_start

            # make sure to give a little wiggle room so you don't
            # kick off the routine multiple times with same keypress
            if not next_available_key_action or next_available_key_action <= loop_start:
                key_pressed = False
                keys = pygame.key.get_pressed()

                if keys[pygame.K_3] and keys[pygame.K_4]:
                    logger.info("3 and 4 pressed")
                    key_pressed = True
                elif keys[pygame.K_1]:
                    logger.info("1 pressed")
                    key_pressed = True
                    refresh_screen = True
                    if self.dog_tracker_module_index > -1:
                        logger.info("Adding feeding")
                elif keys[pygame.K_2]:
                    logger.info("2 pressed")
                    key_pressed = True
                    refresh_screen = True
                    if self.dog_tracker_module_index > -1:
                        logger.info("Adding walk")
                        add_walk(self.dog_tracker_db)
                elif keys[pygame.K_3]:
                    logger.info("3 pressed")
                    key_pressed = True
                    refresh_screen = True
                    if self.dog_tracker_module_index > -1:
                        logger.info("Adding greenie")
                        add_greenie(self.dog_tracker_db)
                elif keys[pygame.K_4]:
                    logger.info("4 pressed")
                    key_pressed = True

                if key_pressed:
                    next_available_key_action = arrow.now(tz=get_system_tz()).shift(
                        seconds=+2
                    )

            if refresh_screen:
                logger.info("Refreshing the screen")
                self.inky.run_once()
                seconds_before_next_update = self.inky.countdown()
                time_to_next_refresh = loop_start.shift(
                    seconds=seconds_before_next_update
                )
                logger.info(f"Time to next refresh: {time_to_next_refresh.format()}")
                refresh_screen = False

            sleep(2)


if __name__ == "main":
    print("Running InkyCalGame in standalone mode")
    inky_game = InkyCalWrapper(
        "C:\\development\\settings.json", render=True, optimize=False
    )
    inky_game.run()
