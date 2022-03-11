# Import the pygame module
from time import sleep

import pygame


# Import pygame.locals for easier access to key coordinates

# Updated to conform to flake8 and black standards

from pygame.locals import (
    K_1,
    K_2,
    K_3,
    K_4,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)


# Initialize pygame
pygame.init()

# Define constants for the screen width and height
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Create the screen object
# The size is determined by the constant SCREEN_WIDTH and SCREEN_HEIGHT
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Variable to keep the main loop running
running = True

# Main loop
while running:
    key1_pressed = False
    key2_pressed = False
    key3_pressed = False
    key4_pressed = False

    # Look at every event in the queue
    for event in pygame.event.get():
        # Did the user hit a key?
        if event.type == KEYDOWN:
            # Was it the Escape key? If so, stop the loop.
            if event.key == K_ESCAPE:
                running = False
            elif event.key == K_1:
                key1_pressed = True
            elif event.key == K_2:
                key2_pressed = True
            elif event.key == K_3:
                key3_pressed = True
            elif event.key == K_4:
                key4_pressed = True
        # Did the user click the window close button? If so, stop the loop.
        elif event.type == QUIT:
            running = False

    if key1_pressed:
        print("1 pressed")
    elif key2_pressed:
        print("2 pressed")
    elif key3_pressed:
        print("3 pressed")
    elif key4_pressed:
        print("4 pressed")

    keys = pygame.key.get_pressed()

    if keys[pygame.K_3] and keys[pygame.K_4]:
        print("3 and 4 pressed")
        # make sure to give a little wiggle room so you don't
        # kick off the routine multiple times with same keypress
        sleep(1)
    # Fill the screen with white
    screen.fill((255, 255, 255))

    # Create a surface and pass in a tuple containing its length and width
    surf = pygame.Surface((50, 50))

    # Give the surface a color to separate it from the background
    surf.fill((0, 0, 0))

    rect = surf.get_rect()
    # This line says "Draw surf onto the screen at the center"
    screen.blit(surf, (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

    pygame.display.flip()

