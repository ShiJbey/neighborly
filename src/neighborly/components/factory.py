# -*- coding: utf-8 -*-
"""
factory.py

Factories for creating more complex components from datafiles
"""
import random
import re
from typing import Any, Dict, List, Tuple

from neighborly.components.business import Business, Services, ServiceTypes
from neighborly.components.character import (
    GameCharacter,
    Gender,
    GenderValue,
    PersonalValue,
    PersonalValues,
)
from neighborly.components.routine import Routine, RoutineEntry, time_str_to_int
from neighborly.core.ecs import Component, IComponentFactory, World
from neighborly.core.name_generation import TraceryNameFactory
from neighborly.core.time import Weekday


class GameCharacterFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        name_generator = world.get_resource(TraceryNameFactory)
        first_name_pattern = kwargs["first_name"]
        last_name_pattern = kwargs["last_name"]
        first_name = name_generator.get_name(first_name_pattern)
        last_name = name_generator.get_name(last_name_pattern)
        return GameCharacter(
            first_name,
            last_name,
        )


class GenderFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        gender_str = kwargs.get("value", "non-binary").lower()

        gender_options = {
            "man": GenderValue.Male,
            "male": GenderValue.Male,
            "female": GenderValue.Female,
            "woman": GenderValue.Female,
            "non-binary": GenderValue.NonBinary,
        }

        return Gender(gender_options[gender_str])


class PersonalValuesFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        rng = world.get_resource(random.Random)
        n_likes: int = kwargs.get("n_likes", 3)
        n_dislikes: int = kwargs.get("n_dislikes", 3)

        traits = [
            str(trait.value)
            for trait in rng.sample(list(PersonalValue), n_likes + n_dislikes)
        ]

        # select likes and dislikes
        high_values = rng.sample(traits, n_likes)

        low_values = list(filter(lambda t: t not in high_values, traits))

        # Generate values for each ([30,50] for high values, [-50,-30] for dislikes)
        values_overrides: Dict[str, int] = {}

        for trait in high_values:
            values_overrides[trait] = rng.randint(30, 50)

        for trait in low_values:
            values_overrides[trait] = rng.randint(-50, -30)

        return PersonalValues(values_overrides)


class ServicesFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        service_list: List[str] = kwargs["services"]
        return Services(set([ServiceTypes.get(s) for s in service_list]))


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
    operating_hours_str: str
        String indicating the operating hours

    Notes
    -----
    The following a re valid formats for the operating hours string
    (1a interval 24HR) ## - ##
        Opening hour - closing hour
        Assumes that the business is open all days of the week
    (1b interval 12HR AM/PM) ## AM - ## PM
        Twelve-hour time interval
    (2 interval-alias) "morning", "day", "night", or ...
        Single string that maps to a preset time interval
        Assumes that the business is open all days of the week
    (3 days + interval) MTWRFSU: ## - ##
        Specify the time interval and the specific days of the
        week that the business is open
    (4 days + interval-alias) MTWRFSU: "morning", or ...
        Specify the days of the week and a time interval for
        when the business will be open

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


class BusinessFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        name_pattern: str = kwargs["name"]
        hours: str = kwargs["hours"]
        owner_type: str = kwargs["owner_type"]
        employee_types: Dict[str, int] = kwargs["employees"]

        name_generator = world.get_resource(TraceryNameFactory)

        return Business(
            name=name_generator.get_name(name_pattern),
            operating_hours=parse_operating_hour_str(hours),
            owner_type=owner_type,
            open_positions=employee_types,
        )


class RoutineFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        routine = Routine()

        presets = kwargs.get("presets")

        if presets == "default":
            at_home = RoutineEntry(20, 8, "home")
            routine.add_entries(
                "at_home_default", [d.value for d in list(Weekday)], at_home
            )

        return routine
