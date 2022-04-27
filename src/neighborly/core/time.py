from __future__ import annotations

from dataclasses import dataclass
from typing import List

HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
DAYS_PER_MONTH = 28
WEEKS_PER_MONTH = 4
MONTHS_PER_YEAR = 12
HOURS_PER_YEAR = HOURS_PER_DAY * DAYS_PER_MONTH * MONTHS_PER_YEAR
DAYS_PER_YEAR = DAYS_PER_MONTH * MONTHS_PER_YEAR

_TIME_OF_DAY: List[str] = [
    *(["night"] * 6),  # (00:00-05:59)
    *(["morning"] * 1),  # (06:00-06:59)
    *(["day"] * 11),  # (07:00-17:59)
    *(["evening"] * 1),  # (18:00-18:59)
    *(["night"] * 5),  # (19:00-23:59)
]

_DAYS_OF_WEEK: List[str] = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def get_time_of_day(hour: int) -> str:
    """Return a string corresponding to the time of day for the given hour"""
    return _TIME_OF_DAY[hour]


@dataclass(frozen=True)
class TimeDelta:
    """Represents a difference in time from one SimDateTime to Another"""
    years: int = 0
    months: int = 0
    days: int = 0
    hours: int = 0

    @property
    def total_days(self) -> int:
        """get the total number of days that this delta represents"""
        return self.days + (self.months * DAYS_PER_MONTH) + (self.years * MONTHS_PER_YEAR * DAYS_PER_MONTH)

    @property
    def total_hours(self) -> int:
        """get the total number of days that this delta represents"""
        return self.hours \
               + (self.days * HOURS_PER_DAY) \
               + (self.months * DAYS_PER_MONTH * HOURS_PER_DAY) \
               + (self.years * MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY)


class SimDateTime:
    """
    Implementation of time in the simulated town
    using 7-day weeks, 4-week months, and 12-month years
    """

    __slots__ = "_hour", "_day", "_month", "_year", "_weekday", "_delta_time"

    def __init__(
            self,
            year: int = 0,
            month: int = 0,
            day: int = 0,
            hour: int = 0,
    ) -> None:
        if 0 <= hour < HOURS_PER_DAY:
            self._hour: int = hour
        else:
            raise ValueError(f"Parameter 'hours' must be between 0 and {HOURS_PER_DAY - 1}")

        if 0 <= day < DAYS_PER_MONTH:
            self._day: int = day
            self._weekday: int = day % 7
        else:
            raise ValueError(f"Parameter 'day' must be between 0 and {DAYS_PER_MONTH - 1}")

        if 0 <= month < MONTHS_PER_YEAR:
            self._month: int = month
        else:
            raise ValueError(f"Parameter 'month' must be between 0 and {MONTHS_PER_YEAR - 1}")

        self._year: int = year
        self._delta_time: int = 0

    def increment(
            self,
            hours: int = 0,
            days: int = 0,
            months: int = 0,
            years: int = 0
    ) -> None:
        """Advance time by a given amount"""

        if hours < 0:
            raise ValueError("Parameter 'hours' may not be negative")
        if days < 0:
            raise ValueError("Parameter 'days' may not be negative")
        if months < 0:
            raise ValueError("Parameter 'months' may not be negative")
        if years < 0:
            raise ValueError("Parameter 'years' may not be negative")

        total_hours: int = self._hour + hours
        carry_days: int = int(total_hours / 24)

        self._hour = total_hours % 24

        self._weekday = (self._weekday + days + carry_days) % 7

        total_days: int = self.day + days + carry_days
        carry_months: int = int(total_days / 28)  # 28 days per month
        self._day = total_days % 28

        total_months: int = self._month + months + carry_months
        carry_years: int = int(total_months / 12)
        self._month = total_months % 12

        self._year = self._year + years + carry_years

        self._delta_time = \
            hours \
            + days * HOURS_PER_DAY \
            + months * DAYS_PER_MONTH * HOURS_PER_DAY \
            + years * MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY

    @property
    def hour(self) -> int:
        return self._hour

    @property
    def day(self) -> int:
        return self._day

    @property
    def weekday(self) -> int:
        return self._weekday

    @property
    def month(self) -> int:
        return self._month

    @property
    def year(self) -> int:
        return self._year

    @property
    def delta_time(self) -> int:
        return self._delta_time

    @property
    def weekday_str(self) -> str:
        return _DAYS_OF_WEEK[self._weekday]

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
        return "{}-{}-{}-{}".format(self.year, self.month, self.day, self.hour)

    def __sub__(self, other: SimDateTime) -> TimeDelta:
        """Subtract a SimDateTime from another and return the difference"""
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
        if not isinstance(other, TimeDelta):
            raise TypeError(f"expected TimeDelta object but was {type(other)}")
        self.increment(hours=other.hours, days=other.days, months=other.months, years=other.years)
        return self

    def __le__(self, other: SimDateTime) -> bool:
        if not isinstance(other, SimDateTime):
            raise TypeError(f"expected TimeDelta object but was {type(other)}")
        return self.to_iso_str() < other.to_iso_str()

    def __gt__(self, other) -> bool:
        if not isinstance(other, SimDateTime):
            raise TypeError(f"expected TimeDelta object but was {type(other)}")
        return self.to_iso_str() > other.to_iso_str()

    def to_date_str(self) -> str:
        return "{}, {:02d}/{:02d}/{:04d} @ {:02d}:00".format(
            self.weekday_str[:3], self.day, self.month, self.year, self.hour
        )

    def to_iso_str(self) -> str:
        """Return ISO string format"""
        return "{:04d}-{:02d}-{:02d}T{:02d}:00.000z".format(
            self.year, self.month, self.day, self.hour
        )

    def to_hours(self) -> int:
        """Return the number of hours that have elapsed since 00-00-0000"""
        return \
            self.hour \
            + (self.day * HOURS_PER_DAY) \
            + (self.month * DAYS_PER_MONTH * HOURS_PER_DAY) \
            + (self.year * MONTHS_PER_YEAR * DAYS_PER_MONTH * HOURS_PER_DAY)

    def to_ordinal(self) -> int:
        """Returns the number of elapsed days since 00-00-0000"""
        return \
            + self.day \
            + (self.month * DAYS_PER_MONTH) \
            + (self.year * MONTHS_PER_YEAR * DAYS_PER_MONTH)

    @classmethod
    def from_ordinal(cls, ordinal_date: int) -> SimDateTime:
        date = cls()
        date.increment(days=ordinal_date)
        return date

    @classmethod
    def from_iso_str(cls, iso_date: str) -> SimDateTime:
        """Return a SimDateTime object given an ISO format string"""
        date_time = iso_date.strip().split('T')
        date = date_time[0]
        time = date_time[1] if len(date_time) == 2 else "00:00.000z"
        year, month, day = tuple(map(lambda s: int(s.strip()), date.split('-')))
        hour = int(time.split(':')[0])
        return cls(year=year, month=month, day=day, hour=hour)

    @classmethod
    def from_str(cls, time_str: str) -> SimDateTime:
        time = cls()
        year, month, day, hour = tuple(time_str.split("-"))
        time._year = int(year)
        time._month = int(month)
        time._weekday = int(day) % 7
        time._day = int(day)
        time._hour = int(hour)
        return time
