#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
9.7" driver class
Copyright by aceisace
"""
import pygame

from inkycal.custom import images, top_level
from os.path import exists
from PIL import Image
import subprocess

# Display resolution
EPD_WIDTH = 1200
EPD_HEIGHT = 825


class EPD:
    def __init__(self):
        # Create the screen object
        self.screen = pygame.display.set_mode((EPD_WIDTH, EPD_HEIGHT))
        # self.screen = pygame.display.set_mode((EPD_HEIGHT, EPD_WIDTH))
        # Fill the screen with white
        self.screen.fill((255, 255, 255))

    def init(self):
        pass

    def display(self, command):
        """displays an image"""
        try:
            # create a surface object, image is drawn on it.
            image = pygame.image.load(command)
            self.screen.blit(image, (0, 0))
            # self.screen.blit(pygame.transform.rotate(self.screen, 90), (0, 0))
            # keep debug screen updated
            pygame.display.flip()
        except Exception as e:
            print("oops, something didn't work right :/")

    def getbuffer(self, image):
        """ad-hoc"""
        image = image.rotate(90, expand=True)
        image_path = images + "canvas.bmp"
        image.convert("RGB").save(image_path, "BMP")
        # print(command)
        return image_path

    def sleep(self):
        pass
