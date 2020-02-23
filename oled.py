import time

import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0


class Oled:
    def __init__(self):
        # 128x32 display with hardware I2C:
        self.disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

        # Initialize library.
        self.disp.begin()

        # Clear display.
        self.disp.clear()
        self.disp.display()

        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self.width = self.disp.width
        self.height = self.disp.height
        self.image = Image.new('1', (self.width, self.height))

        # Get drawing object to draw on image.
        self.draw = ImageDraw.Draw(self.image)

        # Draw a black filled box to clear the image.
        self.draw.rectangle((0,0,self.width,self.height), outline=0, fill=0)

        # Draw some shapes.
        # First define some constants to allow easy resizing of shapes.
        padding = -2
        self.top = padding
        self.bottom = self.height - padding
        # Move left to right keeping track of the current x position for drawing shapes.
        self.x = 0


        # Load default font.
        #font = ImageFont.load_default()

        # Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
        # Some other nice fonts to try: http://www.dafont.com/bitmap.php
        # font = ImageFont.truetype('Minecraftia.ttf', 8)
        self.font = ImageFont.truetype('VCR_OSD_MONO.ttf', 16)

    def clear(self):
        # Draw a black filled box to clear the image.
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def off(self):
        self.disp.clear()
        self.disp.display()

    def print(self, string):
        self.draw.text((self.x, self.top), string, font=self.font, fill=255)

        # Display image.
        self.disp.image(self.image)
        self.disp.display()
