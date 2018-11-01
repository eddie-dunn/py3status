"""Tests for module battery_level"""
# pylint: disable=missing-docstring
# pylint: disable=no-member


# TODO
# - add test for parsing battery output
#   - failing output can be found in github issue
#   - <link>
# - make module work when docked
# - refactor out methods that can be functions

from textwrap import dedent

from py3status.modules import battery_level

ACPI_INFO_DOCKED_CHARGING = dedent(
    """\
    Battery 0: Discharging, 0%, rate information unavailable
    Battery 1: Charging, 44%, 01:04:56 until charged
    Battery 1: design capacity 6842 mAh, last full capacity 6002 mAh = 87%
    Battery 2: Discharging, 0%, rate information unavailable
    """
)

ACPI_INFO_0 = dedent(
    """\
    Battery 0: Discharging, 70%, 06:58:42 remaining
    Battery 0: design capacity 6842 mAh, last full capacity 6002 mAh = 87%
    """
)

ACPI_INFO_1 = dedent(
    # TODO: Add charging battery too
    """\
    Battery 0: Full, 100%
    Battery 0: design capacity 6842 mAh, last full capacity 6002 mAh = 87%
    Battery 1: Discharging, 0%, rate information unavailable
    Battery 2: Discharging, 0%, rate information unavailable
    Battery 3: Discharging, 70%, 06:58:42 remaining
    Battery 3: design capacity 6842 mAh, last full capacity 6002 mAh = 87%
    """
)
ACPI_INFO_2 = dedent(
    """\
    Battery 0: Full, 100%
    Battery 0: design capacity 6842 mAh, last full capacity 6002 mAh = 87%
    Battery 1: Discharging, 70%, 06:58:42 remaining
    Battery 1: design capacity 6842 mAh, last full capacity 6002 mAh = 87%
    """
)

# Ensure refactoring
# Create tests that
# - gets correct output from original method
# - compares output from original method with output from refactored method
#
# Once feature parity is assured, begin enhancing refactored method.
# This is super cautious, prolly not necessary


def test_no_breakage_0():
    """Ensure that output from working example always stays the same"""
    acpi_info = ACPI_INFO_0.splitlines()
    result = battery_level.battery_info_old(acpi_info)
    assert result == [
        {
            'capacity': 6002,
            'charging': False,
            'percent_charged': 70,
            'time_remaining': '06:58:42',
        }
    ]
    # assert result == battery_level.battery_info(ACPI_INFO_0)


def test_no_breakage_1():
    acpi_info = ACPI_INFO_2.splitlines()
    assert battery_level.battery_info_old(acpi_info) == [
        {
            'percent_charged': 100,
            'charging': False,
            'capacity': 6002,
            'time_remaining': '?',
        },
        {
            'capacity': 6002,
            'charging': False,
            'percent_charged': 70,
            'time_remaining': '06:58:42',
        },
    ]


def test_battery_info_0():
    """Ensure that output from working example always stays the same"""
    acpi_info = ACPI_INFO_0
    assert battery_level.battery_info(acpi_info) == [
        {
            'capacity': 6002,
            'charging': False,
            'percent_charged': 70,
            'time_remaining': '06:58:42',
        }
    ]


def test_battery_info_1():
    acpi_info = ACPI_INFO_1
    assert battery_level.battery_info(acpi_info) == [
        {
            'percent_charged': 100,
            'charging': False,
            'capacity': 6002,
            'time_remaining': '?',
        },
        {'charging': False, 'percent_charged': 0, 'time_remaining': '?'},
        {'charging': False, 'percent_charged': 0, 'time_remaining': '?'},
        {
            'capacity': 6002,
            'charging': False,
            'percent_charged': 70,
            'time_remaining': '06:58:42',
        },
    ]
