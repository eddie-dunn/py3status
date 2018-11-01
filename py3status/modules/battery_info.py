# -*- coding: utf-8 -*-
"""
Display battery information.

Configuration parameters:
    battery_id: id of the battery to be displayed
        set to 'all' for combined display of all batteries
        (default 0)
    blocks: a string, where each character represents battery level
        especially useful when using icon fonts (e.g. FontAwesome)
        (default "_▁▂▃▄▅▆▇█")
    cache_timeout: a timeout to refresh the battery state
        (default 30)
    charging_character: a character to represent charging battery
        especially useful when using icon fonts (e.g. FontAwesome)
        (default "⚡")
    format: string that formats the output. See placeholders below.
        (default "{icon}")
    format_notify_charging: format of the notification received when you click
        on the module while your computer is plugged in
        (default 'Charging ({percent}%)')
    format_notify_discharging: format of the notification received when you
        click on the module while your computer is not plugged in
        (default "{time_remaining}")
    hide_seconds: hide seconds in remaining time
        (default False)
    hide_when_full: hide any information when battery is fully charged (when
        the battery level is greater than or equal to 'threshold_full')
        (default False)
    measurement_mode: either 'acpi' or 'sys', or None to autodetect. 'sys'
        should be more robust and does not have any extra requirements, however
        the time measurement may not work in some cases
        (default None)
    notification: show current battery state as notification on click
        (default False)
    notify_low_level: display notification when battery is running low (when
        the battery level is less than 'threshold_degraded')
        (default False)
    sys_battery_path: set the path to your battery(ies), without including its
        number
        (default "/sys/class/power_supply/")
    threshold_bad: a percentage below which the battery level should be
        considered bad
        (default 10)
    threshold_degraded: a percentage below which the battery level should be
        considered degraded
        (default 30)
    threshold_full: a percentage at or above which the battery level should
        should be considered full
        (default 100)

Format placeholders:
    {ascii_bar} - a string of ascii characters representing the battery level,
        an alternative visualization to '{icon}' option
    {icon} - a character representing the battery level,
        as defined by the 'blocks' and 'charging_character' parameters
    {percent} - the remaining battery percentage (previously '{}')
    {time_remaining} - the remaining time until the battery is empty

Color options:
    color_bad: Battery level is below threshold_bad
    color_charging: Battery is charging (default "#FCE94F")
    color_degraded: Battery level is below threshold_degraded
    color_good: Battery level is above thresholds

Requires:
    - the `acpi` command line utility (only if
        `measurement_mode='acpi'`)

@author shadowprince, AdamBSteele, maximbaz, 4iar, m45t3r
@license Eclipse Public License

SAMPLE OUTPUT
{'color': '#FCE94F', 'full_text': u'\u26a1'}

discharging
{'color': '#FF0000', 'full_text': u'\u2340'}
"""

from __future__ import division  # python2 compatibility

import math
import os
from unittest.mock import Mock

BLOCKS = u"_▁▂▃▄▅▆▇█"
FA_BLOCKS = u""
CHARGING_CHARACTER = u"⚡"
EMPTY_BLOCK_CHARGING = u"|"
EMPTY_BLOCK_DISCHARGING = u"⍀"
FULL_BLOCK = u"█"
FORMAT = "{icon}"
FORMAT_NOTIFY_CHARGING = "Charging ({percent}%)"
FORMAT_NOTIFY_DISCHARGING = "{time_remaining}"
SYS_BATTERY_PATH = "/sys/class/power_supply/"
FULLY_CHARGED = "?"
DEFAULT_BATTERY_ID = "BAT0"


class Py3status:
    """
    battery_info
    """

    # available configuration parameters and their defaults
    battery_id = 0
    blocks = BLOCKS
    cache_timeout = 30
    charging_character = CHARGING_CHARACTER
    _format = FORMAT
    format_notify_charging = FORMAT_NOTIFY_CHARGING
    format_notify_discharging = FORMAT_NOTIFY_DISCHARGING
    hide_seconds = False
    hide_when_full = False
    notification = False
    notify_low_level = False
    sys_battery_path = SYS_BATTERY_PATH
    threshold_bad = 10
    threshold_degraded = 30
    threshold_full = 100
    # internal variables
    last_known_status = ""
    py3 = Mock()  # will be replaced
    _is_charging = False
    state = {}

    def post_config_hook(self):
        """Foo"""
        self.last_known_status = ""

    def _refresh_battery_info(self):
        """TODO"""

    def battery_level(self):
        """Return battery level response and does a bunch of other shit"""
        if not os.listdir(self.sys_battery_path):
            return {
                "full_text": "",
                "cached_until": self.py3.time_in(self.cache_timeout),
            }

        self._refresh_battery_info()
        self._update_icon()
        self._update_ascii_bar()
        self._update_full_text()

        return self._build_response()

    def on_click(self, _):
        """
        Display a notification following the specified format
        """
        if not self.notification:
            return

        if self._is_charging:
            _format = self.format_notify_charging
        else:
            _format = self.format_notify_discharging

        message = self.py3.safe_format(
            _format,
            dict(
                ascii_bar=self.ascii_bar,
                icon=self.icon,
                percent=self.state.get("percent_charged"),
                time_remaining=self.state.get("time_remaining"),
            ),
        )

        if message:
            self.py3.notify_user(message, "info")

    def _update_ascii_bar(self):
        self.ascii_bar = FULL_BLOCK * int(self.percent_charged / 10)
        if self.charging:
            self.ascii_bar += EMPTY_BLOCK_CHARGING * (
                10 - int(self.percent_charged / 10)
            )
        else:
            self.ascii_bar += EMPTY_BLOCK_DISCHARGING * (
                10 - int(self.percent_charged / 10)
            )

    def _update_icon(self):
        if self.charging:
            self.icon = self.charging_character
        else:
            self.icon = self.blocks[
                min(
                    len(self.blocks) - 1,
                    int(
                        math.ceil(
                            self.percent_charged / 100 * (len(self.blocks) - 1)
                        )
                    ),
                )
            ]

    def _update_full_text(self):
        self.full_text = self.py3.safe_format(
            self._format,
            dict(
                ascii_bar=self.ascii_bar,
                icon=self.icon,
                percent=self.percent_charged,
                time_remaining=self.time_remaining,
            ),
        )

    def _build_response(self):
        self.response = {}

        self._set_bar_text()
        self._set_bar_color()
        self._set_cache_timeout()

        return self.response

    def _set_bar_text(self):
        self.response["full_text"] = (
            ""
            if self.hide_when_full
            and self.percent_charged >= self.threshold_full
            else self.full_text
        )

    def _set_bar_color(self):
        notify_msg = None
        if self.charging:
            self.response["color"] = self.py3.COLOR_CHARGING or "#FCE94F"
            battery_status = "charging"
        elif self.percent_charged < self.threshold_bad:
            self.response["color"] = self.py3.COLOR_BAD
            battery_status = "bad"
            notify_msg = {
                "msg": "Battery level is critically low ({}%)",
                "level": "error",
            }
        elif self.percent_charged < self.threshold_degraded:
            self.response["color"] = self.py3.COLOR_DEGRADED
            battery_status = "degraded"
            notify_msg = {
                "msg": "Battery level is running low ({}%)",
                "level": "warning",
            }
        elif self.percent_charged >= self.threshold_full:
            self.response["color"] = self.py3.COLOR_GOOD
            battery_status = "full"
        else:
            battery_status = "good"

        if (
            notify_msg
            and self.notify_low_level
            and self.last_known_status != battery_status
        ):
            self.py3.notify_user(
                notify_msg["msg"].format(self.percent_charged),
                notify_msg["level"],
            )

        self.last_known_status = battery_status

    def _set_cache_timeout(self):
        self.response["cached_until"] = self.py3.time_in(self.cache_timeout)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)


"""

    def _extract_battery_information_from_sys(self):

        Extract the percent charged, charging state, time remaining,
        and capacity for a battery, using Linux's kernel /sys interface

        Only available in kernel 2.6.24(?) and newer. Before kernel provided
        a similar, yet incompatible interface in /proc


        def _parse_battery_info(sys_path):
            Extract battery information from uevent file, already convert to
            int if necessary

            raw_values = {}
            with open(os.path.join(sys_path, u"uevent")) as f:
                for var in f.read().splitlines():
                    k, v = var.split("=")
                    try:
                        raw_values[k] = int(v)
                    except ValueError:
                        raw_values[k] = v
            return raw_values

        battery_list = []
        for path in iglob(os.path.join(self.sys_battery_path, "BAT*")):
            r = _parse_battery_info(path)

            capacity = r.get(
                "POWER_SUPPLY_ENERGY_FULL", r.get("POWER_SUPPLY_CHARGE_FULL")
            )
            present_rate = r.get(
                "POWER_SUPPLY_POWER_NOW",
                r.get(
                    "POWER_SUPPLY_CURRENT_NOW",
                    r.get("POWER_SUPPLY_VOLTAGE_NOW"),
                ),
            )
            remaining_energy = r.get(
                "POWER_SUPPLY_ENERGY_NOW", r.get("POWER_SUPPLY_CHARGE_NOW")
            )

            battery = {}
            battery["capacity"] = capacity
            battery["charging"] = "Charging" in r["POWER_SUPPLY_STATUS"]
            battery["percent_charged"] = int(
                math.floor(remaining_energy / capacity * 100)
            )
            try:
                if battery["charging"]:
                    time_in_secs = (
                        (capacity - remaining_energy) / present_rate * 3600
                    )
                else:
                    time_in_secs = remaining_energy / present_rate * 3600
                battery["time_remaining"] = self._seconds_to_hms(time_in_secs)
            except ZeroDivisionError:
                # Battery is either full charged or is not discharging
                battery["time_remaining"] = FULLY_CHARGED

            battery_list.append(battery)
        return battery_list




##

"""
