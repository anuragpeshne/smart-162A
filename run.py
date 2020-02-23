#! /usr/bin/env python3
import os
import json
import time
from datetime import datetime, timedelta

from widget_provider import SysIp, SysInfo, RoomTemp, WebWeather
from oled import Oled

SLEEP_TIMER = 5.0
LOOP_DURATION = timedelta(hours=2)

def splash(display, duration):
    # this is not a fancy feature, this is so that sys gets enough time to startup
    for i in range(duration, -1, -1):
        display.clear()
        display.print("Starting in\n" + str(i) + " seconds")
        time.sleep(1.0)

def loop(display, config):
    sys_ip = SysIp(display)
    sys_info = SysInfo(display)
    #bus_loc = BusLoc()
    room_temp = RoomTemp(display)
    web_weather = WebWeather(display, config)
    #lcd.set_backlight(0)

    enabled_providers = [sys_info, room_temp, web_weather]

    start_time = datetime.now()
    while (True):
        for provider in enabled_providers:
            display.clear()
            display.print(provider.get())
            time.sleep(5.0)
        if datetime.now() - start_time > LOOP_DURATION:
            break

def init(config):
    display = Oled()
    print("Clock started at " + str(datetime.now()))
    splash(display, 3)
    loop(display, config)
    display.off()


if __name__ == "__main__":
    cur_path = os.path.dirname(os.path.realpath(__file__))
    with open(cur_path + "/config.json") as config_file:
        config = json.load(config_file)
    init(config)
