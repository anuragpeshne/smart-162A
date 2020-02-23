#!/usr/bin/env python3

from subprocess import Popen, PIPE, check_output
from time import sleep
from datetime import datetime
import json
import os
import re
import requests
import time

import board
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd

# Modify this if you have a different sized character LCD
lcd_columns = 16
lcd_rows = 2

# compatible with all versions of RPI as of Jan. 2019
# v1 - v3B+
lcd_rs = digitalio.DigitalInOut(board.D27)
lcd_en = digitalio.DigitalInOut(board.D17)
lcd_d4 = digitalio.DigitalInOut(board.D25)
lcd_d5 = digitalio.DigitalInOut(board.D24)
lcd_d6 = digitalio.DigitalInOut(board.D23)
lcd_d7 = digitalio.DigitalInOut(board.D18)
lcd_backlight = digitalio.DigitalInOut(board.D13)

class LcdDisplay:
    def __init__(self):
        self.lcd = characterlcd.Character_LCD_Mono(
            lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6,
            lcd_d7, lcd_columns, lcd_rows)

    def print(self, string):
        self.lcd.message = string

    def clear(self):
        self.lcd.clear()
