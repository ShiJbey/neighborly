from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from neighborly.components.business import Business, OperatingHours
from neighborly.components.routine import time_str_to_int
from neighborly.core.ecs import Component, IComponentFactory, World
from neighborly.core.time import Weekday


class BusinessFactory(IComponentFactory):
    """Constructs instances of Business components"""

    def create(self, world: World, **kwargs: Any) -> Component:
        owner_type: str = kwargs["owner_type"]
        employee_types: Dict[str, int] = kwargs.get("employee_types", {}).copy()

        return Business(
            owner_type=owner_type,
            employee_types=employee_types,
        )


class OperatingHoursFactory(IComponentFactory):
    """Creates instances of OperatingHours components"""

    @staticmethod
    def parse_operating_hour_str(
        operating_hours_str: str,
    ) -> Dict[Weekday, Tuple[int, int]]:
        """
        Convert a string representing the hours of operation
        for a business to a dictionary representing the days
        of the week mapped to tuple time intervals for when
        the business is open.

        Parameters
        ----------
        operating_hours_str
            A text string indicating the operating hours

        Notes
        -----
        The following a re valid formats for the operating hours string:

        - (An 24HR interval) ## - ##, representing Opening hour - closing
          hour, and assumes that the business is open all days of the week.
        - (A 12HR AM/PM interval) ## AM - ## PM, assumes that the business is open all
          days of the week.
        - (interval-alias) "morning", "day", "night", etc, representing a single string
          that maps to a time interval and assumes that the business is open all days of
          the week
        - (days + 24-HR interval) MTWRFSU: ## - ##. Specifies the time interval and the
          specific days of the week that the business is open
        - (days + interval-alias) MTWRFSU: "morning", or ... . Specifies the days of the
          week and a time interval alias for when the business will be open

        Returns
        -------
        Dict[str, Tuple[int, int]]
            Days of the week mapped to lists of time intervals
        """

        interval_aliases = {
            "morning": (5, 12),
            "late-morning": (11, 12),
            "early-morning": (5, 8),
            "day": (8, 11),
            "afternoon": (12, 17),
            "evening": (17, 21),
            "night": (21, 23),
        }

        # time_alias = {
        #     "early-morning": "02:00",
        #     "dawn": "06:00",
        #     "morning": "08:00",
        #     "late-morning": "10:00",
        #     "noon": "12:00",
        #     "afternoon": "14:00",
        #     "evening": "17:00",
        #     "night": "21:00",
        #     "midnight": "23:00",
        # }

        operating_hours_str = operating_hours_str.strip()

        # Check for number interval
        if match := re.fullmatch(
            r"[0-2]?[0-9]\s*(PM|AM)?\s*-\s*[0-2]?[0-9]\s*(PM|AM)?", operating_hours_str
        ):
            interval_strs: List[str] = list(
                map(lambda s: s.strip(), match.group(0).split("-"))
            )

            interval: Tuple[int, int] = (
                time_str_to_int(interval_strs[0]),
                time_str_to_int(interval_strs[1]),
            )

            if 23 < interval[0] < 0:
                raise ValueError(f"Interval start not within bounds [0,23]: {interval}")
            if 23 < interval[1] < 0:
                raise ValueError(f"Interval end not within bounds [0,23]: {interval}")

            return {d: interval for d in list(Weekday)}

        # Check for interval alias
        elif match := re.fullmatch(r"[a-zA-Z]+", operating_hours_str):
            alias = match.group(0)
            if alias in interval_aliases:
                interval = interval_aliases[alias]
                return {d: interval for d in list(Weekday)}
            else:
                raise ValueError(f"Invalid interval alias in: '{operating_hours_str}'")

        # Check for days with number interval
        elif match := re.fullmatch(
            r"[MTWRFSU]+\s*:\s*[0-2]?[0-9]\s*-\s*[0-2]?[0-9]", operating_hours_str
        ):
            days_section, interval_section = tuple(match.group(0).split(":"))
            days_section = days_section.strip()
            interval_strs: List[str] = list(
                map(lambda s: s.strip(), interval_section.strip().split("-"))
            )
            interval: Tuple[int, int] = (int(interval_strs[0]), int(interval_strs[1]))

            if 23 < interval[0] < 0:
                raise ValueError(f"Interval start not within bounds [0,23]: {interval}")
            if 23 < interval[1] < 0:
                raise ValueError(f"Interval end not within bounds [0,23]: {interval}")

            return {Weekday.from_abbr(d): interval for d in days_section.strip()}

        # Check for days with alias interval
        elif match := re.fullmatch(r"[MTWRFSU]+\s*:\s*[a-zA-Z]+", operating_hours_str):
            days_section, alias = tuple(match.group(0).split(":"))
            days_section = days_section.strip()
            alias = alias.strip()
            if alias in interval_aliases:
                interval = interval_aliases[alias]
                return {Weekday.from_abbr(d): interval for d in days_section.strip()}
            else:
                raise ValueError(
                    f"Invalid interval alias ({alias}) in: '{operating_hours_str}'"
                )

        raise ValueError(f"Invalid operating hours string: '{operating_hours_str}'")

    def create(self, world: World, **kwargs: Any) -> Component:
        return OperatingHours({})
