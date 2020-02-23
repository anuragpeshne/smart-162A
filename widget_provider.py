#!/usr/bin/env python3

from subprocess import Popen, PIPE, check_output
import json
import os
import re
import requests
import time

def cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
            cpu_temp_lines = f.readlines()
    cpu_temp_str = cpu_temp_lines[0].strip()
    cpu_temp = str(int(cpu_temp_str) / 1000.0) + " C"
    return cpu_temp

class ProviderBase:
    """
    Takes in display obj.
    The display should support `print` and `clear`
    """
    def __init__(self, display):
        self.display = display
        self.refresh_time = 60
        self.last_refresh_time = int(time.time())
        self.last_str = None

    def get(self):
        if (self.last_str is None or
            (int(time.time()) - self.last_refresh_time) > self.refresh_time):
            print("cache miss")
            self.last_str = self.get_uncached()
            self.last_refresh_time = int(time.time())
        return self.last_str

    def get_uncached(self):
        raise NotImplementedError( "Should have implemented this" )

class RoomTemp(ProviderBase):
    def __init__(self, display):
        ProviderBase.__init__(self, display)

    def room_temp(self):
        temp_str = str(check_output([
            "tail", "-n", "1", "/home/pi/code/tempd/tempdb"]))
        temp = re.search('Temp=(\d+.\d)', temp_str).group(1) + " C"
        humidity = re.search('Humidity=(\d+.\d)', temp_str).group(1) + " %"
        return "Room: " + temp + "\n" + "Humi: " + humidity

    def get_uncached(self):
        return self.room_temp()



class SysIp(ProviderBase):
    def __init__(self, display):
        ProviderBase.__init__(self, display)
        self.refresh_time = 60 * 60 * 12

    def sys_ip(self):
        p1 = Popen(["ifconfig"], stdout=PIPE)
        p2 = Popen(["grep", "inet addr:192"], stdin=p1.stdout, stdout=PIPE)
        p1.stdout.close()
        return re.findall(r"192\.\d+\.\d+.\d+", p2.communicate()[0])[0]

    def get_uncached(self):
        return self.sys_ip()


class SysInfo(ProviderBase):
    def __init__(self, display):
        ProviderBase.__init__(self, display)

    def temp(self):
        p1 = str(check_output(['/opt/vc/bin/vcgencmd', 'measure_temp']))
        return p1[7:11] + " C"

    def get_uncached(self):
        return "Sys: " + self.temp()

class BusLoc(ProviderBase):
    def __init__(self, display):
        ProviderBase.__init__(self, display)
        self.refresh_time = 2 * 60
        self.wait_time_regex = re.compile("wait_time time_1.*Plaza\">(.*)<abbr")

    def time_greenwitch_to_r(self):
        r = requests.get('https://ufl.transloc.com/t/stops/4195938')
        if r.status_code != 200:
            bus_str = 'Unavailable'

        bus_list = re.findall(self.wait_time_regex, r.text)
        if len(bus_list) > 0:
            bus_str = bus_list[0].strip() + ' min'
        else:
            bus_str = 'Unavailable'

        return bus_str

    def get_uncached(self):
        return self.time_greenwitch_to_r()

class WebWeather(ProviderBase):
    def __init__(self, display, config):
        ProviderBase.__init__(self, display)
        self.city_id = 5808079
        self.key = config['keys']['open-weather']
        self.refresh_time = 10 * 60

    def weather_str(self):
        try:
            r = requests.get('http://api.openweathermap.org/data/2.5/weather?id=' +
                             str(self.city_id) +
                             '&appid=' +
                             self.key)
            res = r.json()
            weather_str = ("{:.1f}".format(res['main']['temp_min'] - 273.15) + '<' +
                           "{:.1f}".format(res['main']['temp'] - 273.15) + '<' +
                           "{:.1f}".format(res['main']['temp_max'] - 273.15) + ' C' +
                           '\n' + str(res['main']['humidity']) + '%' +
                           ' | ' + str(res['weather'][0]['main']))
        except requests.exceptions.RequestException:
            weather_str = 'main' + 'NA' + 'curr' + 'NA'
        except KeyError:
            weather_str = 'main' + 'NA' + 'curr' + 'NA'

        return weather_str

    def get_uncached(self):
        return self.weather_str()
