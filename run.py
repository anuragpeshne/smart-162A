#!/usr/bin/env python

import sys, os
import time
from datetime import datetime
import subprocess
import re
import requests
import json

import Queue

if os.environ.get("DISPLAY", None) is None:
    os.environ["DISPLAY"] = ":0"
from pynput import keyboard

import Adafruit_CharLCD as LCD


# Raspberry Pi pin configuration:
lcd_rs        = 25  # Note this might need to be changed to 21 for older revision Pi's.
lcd_en        = 24
lcd_d4        = 23
lcd_d5        = 17
lcd_d6        = 27
lcd_d7        = 22
lcd_backlight = 4

# Define LCD column and row size for 16x2 LCD.
lcd_columns = 16
lcd_rows    = 2

# Initialize the LCD using the pins above.
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,
                           lcd_columns, lcd_rows, lcd_backlight)

# lcd init over

keyQueue = Queue.Queue()

def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(
            key.char))
    except AttributeError:
        print('special key {0} pressed'.format(
            key))

def on_release(key):
    print('{0} released'.format(
        key))
    keyQueue.put(key.char)
    if key == keyboard.Key.esc:
        # Stop listener
        return False

class SysIp:
    def __init__(self):
        self.refresh_time = 60 * 60 * 12
        self.last_refresh_time = int(time.time())
        self.last_ip_str = None

    def get_sys_ip(self):
        if (self.last_ip_str is None or
            (int(time.time()) - self.last_refresh_time) > self.refresh_time):
            p1 = subprocess.Popen(["ifconfig"], stdout=subprocess.PIPE)
            p2 = subprocess.Popen(["grep", "inet addr:192"],
                                  stdin=p1.stdout,
                                  stdout=subprocess.PIPE)
            p1.stdout.close()
            self.last_ip_str = re.findall(r"192\.\d+\.\d+.\d+",
                                            p2.communicate()[0])[0]
            self.last_refresh_time = int(time.time())

        return self.last_ip_str


class SysTemp:
    def __init__(self):
        self.refresh_time = 30
        self.last_refresh_time = int(time.time())
        self.last_temp_str = None

    def get_sys_temp(self):
        if (self.last_temp_str is None or
            (int(time.time()) - self.last_refresh_time) > self.refresh_time):
            p1 = subprocess.check_output(['/opt/vc/bin/vcgencmd', 'measure_temp'])
            self.last_temp_str = p1[5:].strip()
            self.last_refresh_time = int(time.time())

        return self.last_temp_str

class BusLoc:
    def __init__(self):
        self.refresh_time = 2 * 60
        self.last_refresh_time = int(time.time())
        self.last_time_str = None
        self.wait_time_regex = re.compile("wait_time time_1.*Plaza\">(.*)<abbr")
    def get_time_greenwitch_to_r(self):
        if (self.last_time_str is None or
            (int(time.time()) - self.last_refresh_time) > self.refresh_time):
            self.last_refresh_time = int(time.time())

            r = requests.get('https://ufl.transloc.com/t/stops/4195938')
            if r.status_code != 200:
                self.last_time_str = 'Unavailable'

            bus_list = re.findall(self.wait_time_regex, r.text)
            if len(bus_list) > 0:
                self.last_time_str = bus_list[0].strip() + ' min'
            else:
                self.last_time_str = 'Unavailable'

        return self.last_time_str

class WebWeather:
    def __init__(self, config):
        self.gainesville_id = 4692748
        self.key = config['keys']['open-weather']
        self.refresh_time = 10 * 60
        self.last_refresh_time = None
        self.last_weather_res = None
        self.last_forecast_res = None

    def now(self):
        if (self.last_weather_res is None or
            (int(time.time()) - self.last_refresh_time) > self.refresh_time):
            r = requests.get('http://api.openweathermap.org/data/2.5/weather?id=' +
                             str(self.gainesville_id) +
                             '&appid=' +
                             self.key)
            if r.status_code != 200:
                self.last_weather_res = None

            res = r.json()
            try:
                self.last_weather_res = {
                        'main': res['weather'][0]['main'],
                        'curr': (res['main']['temp'] - 273.15)
                }
            except KeyError:
                self.last_weather_res = {
                    'main': 'NA',
                    'curr': 'NA'
                }

            self.last_refresh_time = int(time.time())
        return self.last_weather_res

    def forecast(self):
        #since this is forecast, 10X refresh time
        if (self.last_forecast_res is None or
            (int(time.time()) - self.last_refresh_time) > (self.refresh_time * 10)):
            r = requests.get('http://api.openweathermap.org/data/2.5/forecast?id=' +
                             str(self.gainesville_id) +
                             '&appid=' +
                             self.key)
            if r.status_code != 200:
                self.last_weather_res = None

            res = r.json()
            try:
                self.last_forecast_res = {
                        'main': res['list'][0]['weather'][0]['main'],
                        'desc': res['list'][0]['weather'][0]['description']
                }
            except KeyError:
                self.last_forecast_res = {
                    'main': 'NA',
                    'curr': 'NA'
                }
            self.last_refresh_time = int(time.time())
        return self.last_forecast_res

def splash():
    # this is not a fancy feature, this is so that sys gets enough time to startup
    for i in range(10):
        lcd.clear()
        lcd.message("Starting in\n" + str(10 - i) + " seconds")
        time.sleep(1.0)

def shutdown():
    print "Shutting down"
    lcd.clear()
    lcd.message("Bye!")
    os.system("sudo shutdown -h now")

def loop(config):
    sys_ip = SysIp()
    sys_temp = SysTemp()
    bus_loc = BusLoc()
    web_weather = WebWeather(config)
    #lcd.set_backlight(0)

    while (True):
        lcd.clear()
        timestr = datetime.now().strftime('%a %b %d\n%H:%M %p')
        temp = web_weather.now()['curr']
        lcd.message(timestr + ' ' + str(temp) + 'C')

        # Wait 5 seconds
        time.sleep(8.0)

        lcd.clear()
        lcd.message("IP:" + sys_ip.get_sys_ip() + "\n" +
                    "Sys temp:" + sys_temp.get_sys_temp())
        time.sleep(4.0)

        lcd.clear()
        lcd.message("-> Reitz:\n" + bus_loc.get_time_greenwitch_to_r())
        time.sleep(6.0)

        lcd.clear()
        forecast = web_weather.forecast()
        lcd.message(forecast['main'] + '\n' + forecast['desc'])
        time.sleep(6.0)

        if not keyQueue.empty():
            key = keyQueue.get()
            if key == 's':
                shutdown()

if __name__ == "__main__":
    with keyboard.Listener(on_release=on_release) as listener:
        try:
            print "Clock started at " + str(datetime.now())
            sys.stdout.flush()
            splash()
            cur_path = os.path.dirname(os.path.realpath(__file__))
            with open(cur_path + "/config.json") as config_file:
                config = json.load(config_file)
            loop(config)
        finally:
            listener.stop()
