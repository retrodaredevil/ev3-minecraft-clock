#!/usr/bin/env python3

import sys
import time
from datetime import datetime

from ev3dev.ev3 import *

BE_WITHIN = 5  # The deadzone in degrees. Motor won't try to move if current position within
buttons = Button()


class Clock:
    def __init__(self, motor, gear_ratio=1.0):
        self.motor = motor
        self.gear_ratio = gear_ratio
        self.origin = 0  # in degrees
        self.speed = 45

        self.full_rotation = self.motor.count_per_rot

    def to_degrees(self, value):
        """
        :param value: The encoder value
        :return: The value in degrees of the encoder value
        """
        return (value / self.full_rotation) * 360

    def to_encoder(self, value):
        """
        :param value: The value in degrees
        :return: The value in encoder counts
        """
        return (value / 360.0) * self.full_rotation

    def set_origin_here(self):
        self.origin = self.to_degrees(self.motor.position)

    def get_position(self):  # in degrees
        r = (self.to_degrees(self.motor.position) - self.origin)
        r *= self.gear_ratio
        return r

    def set_position(self, value):  # value should be in degrees
        value /= self.gear_ratio
        value = value + self.origin
        value = self.to_encoder(value)
        self.motor.run_to_abs_pos(position_sp=value, speed_sp=self.speed)
        while len(self.motor.state) != 0:
            time.sleep(0.5)  # wait until we are done moving


def start(clock):
    remote = RemoteControl(channel=1)
    hour_adjust = -5  # subtract 5 to go from GMT to Central Time
    last_hour = None
    times_through = 0

    while True:
        now = datetime.now()  # gets system time
        hour = (now.hour + hour_adjust) % 24
        if last_hour is not None and last_hour > hour:
            times_through += 1  # when it is midnight, the clock won't rotate back
        last_hour = hour
        minute = now.minute

        position = (hour + (minute / 60.0)) / 24.0   # 0 to 1
        position += times_through
        position *= 360
        position = round(position / BE_WITHIN) * BE_WITHIN  # less work for motor
        
        if abs(clock.get_position() - position) >= BE_WITHIN:
            clock.set_position(position)
            print("position: {}, hour: {}, minute: {}".format(position, hour, minute))

        sleep_time = 0.1
        for i in range(int(10 / sleep_time)):
            time.sleep(sleep_time)  # take some load off the CPU
            if buttons.backspace:
                sys.exit(0)
            if remote.connected:
                if remote.red_up:
                    say_time(hour, minute)
                elif remote.red_down:
                    Sound.speak("oink").wait()
                elif remote.blue_up:
                    Sound.speak("butter, do you know the way butter?").wait()
                elif remote.blue_down:
                    Sound.speak("I tell the time. What do you do?").wait()


def say_time(hour, minute):
    hour = hour % 24
    pm = hour >= 12
    if pm and hour != 12:
        hour -= 12
    if hour == 0:
        pm = False
        hour = 12
    pm_string = "P M" if pm else "Aaa M"
    if minute == 0:
        Sound.speak("{} Oh Clock {}".format(hour, pm_string))
        return
    minute_string = str(minute) if minute >= 10 else "Oh {}".format(minute)
    Sound.speak("{} , {} {}".format(hour, minute_string, pm_string)).wait()


def main():
    # thanks https://sites.google.com/site/ev3python/learn_ev3_python/leds
    Leds.all_off()  # turn off all leds
    motor = MediumMotor("outA")

    clock = Clock(motor, gear_ratio=(1.0/3.0))
    clock.set_origin_here()
    start(clock)


if __name__ == '__main__':
    main()
