"""
A Python module created to interact with the Velleman K8055 kit

Created By Fergus Leahy a.k.a. Fergul Magurgul
(https://sourceforge.net/projects/pyk8055/)

Copyright (C) 2010  Fergus Leahy (http://py-hole.blogspot.com)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

#  - Requires K8055D.dll to be in the same directory/folder.

from ctypes import *


def log(message, end=None):
    # print(message, end=end)
    pass


class device:
    def __init__(self, port=0):
        log("Loading K8055 dll...", end=' ')
        try:
            self.lib = WinDLL("./K8055D.dll")
            log("done.")
        except:
            print("failed!")
            print("Failed to find K8055d.dll in local folder.")
            return
        log("Accessing the device on port %d..." % port, end=' ')
        self.lib.OpenDevice(port)
        log("done.")

    def disconnect(self):
        log("Disconnecting the device...", end=' ')
        self.lib.CloseDevice()
        log("done.")

    def analog_in(self, channel):
        log("Checking analogue channel %d..." % channel, end=' ')
        status = self.lib.ReadAnalogChannel(channel)
        log("done.")
        return status

    def analog_all_in(self):
        data1, data2 = c_int(), c_int()
        log("Checking all analogue channels...", end=' ')
        self.lib.ReadAllAnalog(byref(data1), byref(data2))
        log("done.")
        return data1.value, data2.value

    def analog_clear(self, channel):
        log("Clearing analogue channel %d..." % channel, end=' ')
        self.lib.ClearAnalogChannel(channel)
        log("done.")

    def analog_all_clear(self):
        log("Clearing both analogue channels...", end=' ')
        self.lib.ClearAllAnalog()
        log("done.")

    def analog_out(self, channel, value):
        log("Changing the value of analogue channel %d to %d..." % (channel, value), end=' ')
        if 0 <= value <= 255:
            self.lib.OutputAnalogChannel(channel, value)
            log("done.")
        else:
            log()
            log("Value must be between (inclusive) 0 and 255")

    def analog_all_out(self, data1, data2):
        log("Changing the value of both analogue channels...", end=' ')
        if 0 <= data1 <= 255 and 0 <= data2 <= 255:
            self.lib.OutputAllAnalog(data1, data2)
            log("done.")
        else:
            log()
            log("Value must be between (inclusive) 0 and 255")

    def digital_write(self, data):
        log("Writing %d to digital channels..." % data, end=' ')
        self.lib.WriteAllDigital(data)
        log("done.")

    def digital_off(self, channel):
        log("Turning digital channel %d OFF..." % channel, end=' ')
        self.lib.ClearDigitalChannel(channel)
        log("done.")

    def digital_all_off(self):
        log("Turning all digital channels OFF...", end=' ')
        self.lib.ClearAllDigital()
        log("done.")

    def digital_on(self, channel):
        log("Turning digital channel %d ON..." % channel, end=' ')
        self.lib.SetDigitalChannel(channel)
        log("done.")

    def digital_all_on(self):
        log("Turning all digital channels ON...", end=' ')
        self.lib.SetAllDigital()
        log("done.")

    def digital_in(self, channel):
        log("Checking digital channel %d..." % channel, end=' ')
        status = self.lib.ReadDigitalChannel(channel)
        log("done.")
        return status

    def digital_all_in(self):
        log("Checking all digital channels...", end=' ')
        status = self.lib.ReadAllDigital()
        log("done.")
        return status

    def counter_reset(self, channel):
        log("Reseting Counter value...", end=' ')
        self.lib.ResetCounter(channel)
        log("done,")

    def counter_read(self, channel):
        log("Reading Counter value from counter %d..." % channel, end=' ')
        status = self.lib.ReadCounter(channel)
        log("done.")
        return status

    def counter_set_debounce(self, channel, time):
        if 0 <= time <= 5000:
            log("Setting Counter %d's debounce time to %dms..." % (channel, time), end=' ')
            self.lib.SetCounterDebounceTime(channel, time)
            log("done.")
        else:
            log("Time must be between 0 and 5000ms (inclusive).")
