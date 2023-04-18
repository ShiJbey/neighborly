"""Neighborly Simulation DateTime

Neighborly uses a custom date/time implementation that represents years as 12 months
with 4, 7-day weeks per month. The smallest unit of time is one hour. This module
contains the implementation of simulation datetime along with associated constants,
enums, and helper classes.

"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import IntEnum
from typing import List

HOURS_PER_DAY = 24
"""The number of hours per day."""

DAYS_PER_WEEK = 7
"""The number of days per week."""

DAYS_PER_MONTH = 28
"""The number of days per month."""

WEEKS_PER_MONTH = 4
"""The number of weeks per month."""

MONTHS_PER_YEAR = 12
"""The number of months per year."""

HOURS_PER_YEAR = HOURS_PER_DAY * DAYS_PER_MONTH * MONTHS_PER_YEAR
"""The number of hours per year."""

DAYS_PER_YEAR = DAYS_PER_MONTH * MONTHS_PER_YEAR
"""The number of days per year."""

_TIME_OF_DAY: List[str] = [
    *(["night"] * 6),  # (00:00-05:59)
    *(["morning"] * 1),  # (06:00-06:59)
    *(["day"] * 11),  # (07:00-17:59)
    *(["evening"] * 1),  # (18:00-18:59)
    *(["night"] * 5),  # (19:00-23:59)
]
"""List of hour slots holding the time-of-day for that hour."""


class Weekday(IntEnum):
    """Enumeration of the days of the week."""

    Sunday = 0
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6

    def __str__(self) -> str:
        return self.name

    def abbr(self) -> str:
        """Get the one-character abbreviation of the weekday.

        Returns
        -------
        str
            The abbreviation.
        """
        abbreviations = [
            "U",
            "M",
            "T",
            "W",
            "R",
            "F",
            "S",
        ]
        return abbreviations[int(self)]

    @classmethod
    def from_abbr(cls, value: str) -> Weekday:
        """Convert weekday abbreviation to Weekday value.

        Returns
        -------
        Weekday
            The corresponding weekday value.
        """
        abbreviations = {
            "M": Weekday.Monday,
            "T": Weekday.Tuesday,
            "W": Weekday.Wednesday,
            "R": Weekday.Thursday,
            "F": Weekday.Friday,
            "S": Weekday.Saturday,
            "U": Weekday.Sunday,
        }
        return abbreviations[value]


@dataclass(frozen=True)
class TimeDelta:
    """Represents a difference in time from one SimDateTime to Another."""

    years: int = 0
    """A number of years."""

    months: int = 0
    """A number of months."""

    days: int = 0
    """A number of days."""

    hours: int = 0
    """A number of hours."""

    @property
    def total_days(self) -> int:
        """The total number of days that this delta represents."""
        return (
            self.days
            + (self.months * DAYS_PER_MONTH)
            + (self.years * MONTHS_PER_YEAR * DAYS_PER_MONTH)
        )

    @property
    def total_hours(self) -> int:
        """The total number of hours that this delta represents."""
        return (
            self.hours
            + (self.days * HOURS_PER_DAY)
            + (self.months * DAYS_PER_MONTH * HOURS_PER_DAY)
            + (self.years * MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY)
        )


class SimDateTime:
    """A custom implementation of datetime for the simulation.

    This class implements 24-hour days with 7-days per week, 4-weeks per month, and
    12-months per year.
    """

    __slots__ = "_hour", "_day", "_month", "_year", "_weekday"

    _hour: int
    """The current hour."""

    _day: int
    """The current day of the month."""

    _month: int
    """The current month of the year."""

    _year: int
    """The current year."""

    _weekday: Weekday
    """The current day of the week."""

    def __init__(
        self,
        year: int = 1,
        month: int = 1,
        day: int = 1,
        hour: int = 0,
    ) -> None:
        """
        Parameters
        ----------
        year
            The starting year (must be >= 1), by default 1
        month
            The starting month (must be >= 1 <= 12), by default 1
        day
            The starting day (must be >= 1 and <= 28), by default 1
        hour
            The starting hour (must be >= 0 and < 24), by default 0
        """
        if 0 <= hour < HOURS_PER_DAY:
            self._hour = hour
        else:
            raise ValueError(
                f"Parameter 'hours' must be between 0 and {HOURS_PER_DAY - 1}"
            )

        if 1 <= day <= DAYS_PER_MONTH:
            self._day = day - 1
            self._weekday = Weekday(self._day % 7)
        else:
            raise ValueError(f"Parameter 'day' must be between 1 and {DAYS_PER_MONTH}")

        if 1 <= month <= MONTHS_PER_YEAR:
            self._month = month - 1
        else:
            raise ValueError(
                f"Parameter 'month' must be between 1 and {MONTHS_PER_YEAR}"
            )

        if year < 1:
            raise ValueError("Parameter 'year' must be greater than or equal to 1.")
        self._year = year - 1

    def increment(
        self, hours: int = 0, days: int = 0, months: int = 0, years: int = 0
    ) -> None:
        """Advance time by a given amount.

        Parameters
        ----------
        hours
            The number of hours to advance.
        days
            The number of days to advance.
        months
            The number of months to advance.
        years
            The number of years to advance.
        """

        if hours < 0:
            raise ValueError("Parameter 'hours' may not be negative")
        if days < 0:
            raise ValueError("Parameter 'days' may not be negative")
        if months < 0:
            raise ValueError("Parameter 'months' may not be negative")
        if years < 0:
            raise ValueError("Parameter 'years' may not be negative")

        total_hours: int = self._hour + hours
        carry_days: int = total_hours // HOURS_PER_DAY

        self._hour = total_hours % HOURS_PER_DAY

        total_days: int = self._day + days + carry_days

        carry_months: int = total_days // DAYS_PER_MONTH

        self._day = total_days % DAYS_PER_MONTH

        self._weekday = Weekday(self._day % DAYS_PER_WEEK)

        total_months: int = self._month + months + carry_months
        carry_years: int = total_months // MONTHS_PER_YEAR

        self._month = total_months % MONTHS_PER_YEAR

        self._year = self._year + years + carry_years

    @property
    def hour(self) -> int:
        """The current hour."""
        return self._hour

    @property
    def day(self) -> int:
        """The current day."""
        return self._day + 1

    @property
    def weekday(self) -> Weekday:
        """The current weekday."""
        return self._weekday

    @property
    def month(self) -> int:
        """The current month."""
        return self._month + 1

    @property
    def year(self) -> int:
        """The current year."""
        return self._year + 1

    @property
    def weekday_str(self) -> str:
        """The name of the current weekday."""
        return str(Weekday(self._weekday))

    def copy(self) -> SimDateTime:
        """Creates a copy of the date.

        Returns
        -------
        SimDateTime
            A copy of the calling object.
        """
        return SimDateTime(
            hour=self.hour,
            day=self.day,
            month=self.month,
            year=self.year,
        )

    def __repr__(self) -> str:
        return "{}(hour={}, day={}, month={}, year={}, weekday={})".format(
            self.__class__.__name__,
            self.hour,
            self.day,
            self.month,
            self.year,
            self.weekday_str,
        )

    def __str__(self) -> str:
        return self.to_iso_str()

    def __sub__(self, other: SimDateTime) -> TimeDelta:
        """Subtract a SimDateTime from another and return the difference."""
        diff_hours = self.to_hours() - other.to_hours()

        # Convert hours back to date components
        remainder: int = diff_hours
        years = remainder // (MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY)
        remainder = remainder % (MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY)
        months = remainder // (DAYS_PER_MONTH * HOURS_PER_DAY)
        remainder = remainder % (DAYS_PER_MONTH * HOURS_PER_DAY)
        days = remainder // HOURS_PER_DAY
        hours = remainder % HOURS_PER_DAY

        return TimeDelta(years=years, months=months, days=days, hours=hours)

    def __add__(self, other: TimeDelta) -> SimDateTime:
        """Add a TimeDelta to this data"""
        date_copy = self.copy()
        date_copy.increment(
            hours=other.hours, days=other.days, months=other.months, years=other.years
        )
        return date_copy

    def __iadd__(self, other: TimeDelta) -> SimDateTime:
        self.increment(
            hours=other.hours, days=other.days, months=other.months, years=other.years
        )
        return self

    def __le__(self, other: SimDateTime) -> bool:
        return self.to_hours() <= other.to_hours()

    def __lt__(self, other: SimDateTime) -> bool:
        return self.to_hours() < other.to_hours()

    def __ge__(self, other: SimDateTime) -> bool:
        return self.to_hours() >= other.to_hours()

    def __gt__(self, other: SimDateTime) -> bool:
        return self.to_hours() > other.to_hours()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimDateTime):
            raise TypeError(f"expected SimDateTime object but was {type(other)}")
        return self.to_hours() == other.to_hours()

    def to_date_str(self) -> str:
        """Create a date string.

        Returns
        -------
        str
            A date string of the format WEEKDAY, DD/MM,YYY @ HH:00
        """
        return "{}, {:02d}/{:02d}/{:04d} @ {:02d}:00".format(
            self.weekday_str[:3], self.day, self.month, self.year, self.hour
        )

    def to_iso_str(self) -> str:
        """Create an ISO date string.

        Returns
        -------
        str
            The date string.
        """
        return "{:04d}-{:02d}-{:02d}T{:02d}:00:00".format(
            self.year, self.month, self.day, self.hour
        )

    def to_hours(self) -> int:
        """Get the number of hours that have elapsed since 01-01-0001 12:00 AM.

        Returns
        -------
        int
            The total amount of hours.
        """
        return (
            self.hour
            + (self._day * HOURS_PER_DAY)
            + (self._month * DAYS_PER_MONTH * HOURS_PER_DAY)
            + (self._year * MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY)
        )

    def get_time_of_day(self) -> str:
        """Return a string corresponding to the time of day for the given hour.

        Returns
        -------
        str
            The current time of day.
        """
        return _TIME_OF_DAY[self.hour]

    @classmethod
    def from_str(cls, time_str: str) -> SimDateTime:
        """Create a new SimDateTime instance from a date string.

        Parameters
        ----------
        time_str
            A date in DD/MM/YYYY format or YYYY-MM-DDTHH:00:00 ISO 8061 format

        Returns
        -------
        SimDateTime
            A date object set to the date in the string
        """
        if m := re.match(
            "^(?P<DAY>[0-9]{1,2})\\/(?P<MONTH>[0-9]{1,2})\\/(?P<YEAR>[0-9]{4}$)",
            time_str,
        ):
            return cls(
                year=int(m.group("YEAR")),
                month=int(m.group("MONTH")),
                day=int(m.group("DAY")),
            )

        elif m := re.match(
            (
                "^(?P<YEAR>\\d{4})-(?P<MONTH>\\d{2})-(?P<DAY>\\d{2})"
                "T(?P<HOUR>\\d{2}):(?:\\d{2}):(?:\\d{2}(?:\\.\\d*)?)"
                "(?:(?:-(?:\\d{2}):(?:\\d{2})|Z)?)$"
            ),
            time_str,
        ):
            return cls(
                year=int(m.group("YEAR")),
                month=int(m.group("MONTH")),
                day=int(m.group("DAY")),
                hour=int(m.group("HOUR")),
            )

        else:
            raise ValueError(f"Invalid date string: {time_str}")
