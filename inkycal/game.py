import logging
import os

import arrow
import pygame

from pygame.locals import (
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

import inkycal.modules
from inkycal.custom import get_system_tz
from main import Inkycal

filename = os.path.basename(__file__).split(".py")[0]
logger = logging.getLogger(filename)

# Initialize pygame
pygame.init()
inky = Inkycal(
    settings_path="C:\\development\\settings.json", render=True, optimize=False
)
dog_tracker_module_index = -1
for ix, module in enumerate(inky.modules):
    print(f"Module {ix}: {module.name}")
    if type(module) is inkycal.modules.DogTracker:
        dog_tracker_module_index = ix
        break

# inky.test()
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
        print(
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
            print("3 and 4 pressed")
            key_pressed = True
        elif keys[pygame.K_1]:
            print("1 pressed")
            key_pressed = True
            refresh_screen = True
            if dog_tracker_module_index > -1:
                print("Adding feeding")
                inky.modules[dog_tracker_module_index].add_feeding()
        elif keys[pygame.K_2]:
            print("2 pressed")
            key_pressed = True
            refresh_screen = True
            if dog_tracker_module_index > -1:
                print("Adding walk")
                inky.modules[dog_tracker_module_index].add_walk()
        elif keys[pygame.K_3]:
            print("3 pressed")
            key_pressed = True
            refresh_screen = True
            if dog_tracker_module_index > -1:
                print("Adding greenie")
                inky.modules[dog_tracker_module_index].add_greenie()
        elif keys[pygame.K_4]:
            print("4 pressed")
            key_pressed = True

        if key_pressed:
            next_available_key_action = arrow.now(tz=get_system_tz()).shift(seconds=+2)

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
        print("Refreshing the screen")
        inky.run_once()
        seconds_before_next_update = inky.countdown()
        time_to_next_refresh = loop_start.shift(seconds=seconds_before_next_update)
        print(f"Time to next refresh: {time_to_next_refresh.format()}")
        refresh_screen = False

    pygame.display.flip()
