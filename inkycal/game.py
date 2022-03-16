import logging
import os
from logging.handlers import RotatingFileHandler

import arrow
import pygame

from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

import inkycal.modules
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


class InkyCalGame:
    def __init__(self, settings_path="/boot/settings.json", render=True, optimize=True):
        # Initialize pygame
        pygame.init()
        self.inky = Inkycal(
            settings_path=settings_path, render=render, optimize=optimize
        )
        self.dog_tracker_module_index = -1
        for ix, module in enumerate(self.inky.modules):
            logger.info(f"Module {ix}: {module.name}")
            if type(module) is inkycal.modules.DogTracker:
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
                        self.inky.modules[self.dog_tracker_module_index].add_feeding()
                elif keys[pygame.K_2]:
                    logger.info("2 pressed")
                    key_pressed = True
                    refresh_screen = True
                    if self.dog_tracker_module_index > -1:
                        logger.info("Adding walk")
                        self.inky.modules[self.dog_tracker_module_index].add_walk()
                elif keys[pygame.K_3]:
                    logger.info("3 pressed")
                    key_pressed = True
                    refresh_screen = True
                    if self.dog_tracker_module_index > -1:
                        logger.info("Adding greenie")
                        self.inky.modules[self.dog_tracker_module_index].add_greenie()
                elif keys[pygame.K_4]:
                    logger.info("4 pressed")
                    key_pressed = True

                if key_pressed:
                    next_available_key_action = arrow.now(tz=get_system_tz()).shift(
                        seconds=+2
                    )

            # Look at every event in the queue
            for event in pygame.event.get():
                # Did the user hit a key?
                if event.type == KEYDOWN:
                    # Was it the Escape key? If so, stop the loop.
                    if event.key == K_ESCAPE:
                        running = False
                # Did the user click the window close button? If so, stop the loop.
                elif event.type == QUIT:
                    running = False

            if refresh_screen:
                logger.info("Refreshing the screen")
                self.inky.run_once()
                seconds_before_next_update = self.inky.countdown()
                time_to_next_refresh = loop_start.shift(
                    seconds=seconds_before_next_update
                )
                logger.info(f"Time to next refresh: {time_to_next_refresh.format()}")
                refresh_screen = False

            pygame.display.flip()


if __name__ == "main":
    print("Running InkyCalGame in standalone mode")
    inky_game = InkyCalGame(
        "C:\\development\\settings.json", render=True, optimize=False
    )
    inky_game.run()
