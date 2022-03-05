from typing import List, cast

from neighborly.core.ecs import System

HOURS_PER_DAY = 24
DAYS_PER_WEEK = 7
DAYS_PER_MONTH = 28
WEEKS_PER_MONTH = 4
MONTHS_PER_YEAR = 12
HOURS_PER_YEAR = HOURS_PER_DAY * DAYS_PER_MONTH * MONTHS_PER_YEAR

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


class SimDateTime:
    """
    Implementation of time in the simulated town
    using 7-day weeks, 4-week months, and 12-month years
    """

    __slots__ = "_hour", "_day", "_month", "_year", "_weekday"

    def __init__(self) -> None:
        self._hour: int = 0
        self._day: int = 0
        self._month: int = 0
        self._year: int = 0
        self._weekday: int = 0

    def increment(
            self, hours: int = 0, days: int = 0, months: int = 0, years: int = 0
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

    def to_date_str(self) -> str:
        return "{}, {:02d}/{:02d}/{:04d} @ {:02d}:00".format(
            self.weekday_str[:3], self.day, self.month, self.year, self.hour
        )

    def to_iso_str(self) -> str:
        """Return ISO string format"""
        return "{:04d}-{:02d}-{:02d}T{:02d}:00.000z".format(
            self.year, self.month, self.day, self.hour
        )

    @classmethod
    def from_str(cls, time_str: str) -> "SimDateTime":
        time = cls()
        year, month, day, hour = tuple(time_str.split("-"))
        time._year = int(year)
        time._month = int(month)
        time._weekday = int(day) % 7
        time._day = int(day)
        time._hour = int(hour)
        return time


class TimeProcessor(System):

    def process(self, *args, **kwargs):
        delta_time: int = kwargs["delta_time"]
        sim_time = self.world.get_resource(SimDateTime)
        sim_time = cast(SimDateTime, sim_time)
        sim_time.increment(hours=delta_time)
