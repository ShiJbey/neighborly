import random
from pathlib import Path
from typing import Any, Callable, Dict, NamedTuple, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from neighborly.core.activity import get_top_activities

from neighborly.core.relationship import Relationship
from neighborly.core.character.values import CharacterValues, generate_character_values

AnyPath = Union[str, Path]


@dataclass(frozen=True)
class LifeCycleConfig:
    """Configuration parameters for a characters lifecycle

    Fields
    ------
    lifespan_mean: int
        Average lifespan of characters with this configuration
    lifespan_std: int
        Standard deviation of the lifespans of characters with this
        configuration
    adult_age: int
        Age that characters with thi config are considered adults
        in society
    """
    lifespan_mean: int = 85
    lifespan_std: int = 15
    adult_age: int = 18


@dataclass(frozen=True)
class CharacterConfig:
    """Configuration parameters for characters

    Fields
    ------
    masculine_names: str
        Name of the registered factory that creates instances
        of names that are considered to be more masculine
    feminine_names: str
        Name of the registered factory that creates instances
        of names that are considered to be more feminine
    neutral_names: str
        Name of registered factory that creates instances
        of names that are considered to be more neutral
    surnames: str
        Name of registered factory that creates instances
        of character surnames
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    """
    masculine_names: str = 'default'
    feminine_names: str = 'default'
    neutral_names: str = 'default'
    surnames: str = 'default'
    lifecycle: LifeCycleConfig = field(default_factory=LifeCycleConfig)


class CharacterName(NamedTuple):
    firstname: str
    surname: str

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class Gender(Enum):
    MASCULINE = 0
    FEMININE = 1
    NEUTRAL = 2


class GameCharacter:
    """The state of a single character within the world


    Class Attributes
    ----------------
    _masculine_firstname_factories: Dict[str, Callable[..., str]]
        Dict of functions that generate strings to be masculine names
    _feminine_firstname_factories: Dict[str, Callable[..., str]]
        Dict of functions that generate strings to be feminine names
    _neutral_firstname_factories: Dict[str, Callable[..., str]]
        Dict of functions that generate strings to be gender-neutral names
    _surname_factories: Dict[str, Callable[..., str]]
        Dict of functions that generate strings to be surnames

    Instance Attributes
    -------------------
    config: CharacterConfig
        Configuration settings for the character
    name: CharacterName
        The character's name
    age: float
        The character's current age in years
    _max_age: float
        The age that this character is going to die of natural causes
    gender: Gender
        Loose gender identity for the character
    can_get_pregnant: bool
        Can this character bear children
    location: int
        Entity ID of the location where this character current is
    location_aliases: Dict[str, int]
        Maps string names to entity IDs of locations in the world
    relationships: Dict[int, Relationship]
        Maps characters' entity IDs to Relationships that this
        character has with them
    likes: Tuple[str, ...]
        Names of activities that this character likes to do
    values: CharacterValues
        This characters beliefs/values in life (i.e. loyalty, family, wealth)
    """

    __slots__ = "config", "name", "age", "_max_age", "gender", "can_get_pregnant", \
        "location", "location_aliases", "relationships", "values", "likes",

    _masculine_firstname_factories: Dict[str, Callable[..., str]] = {}
    _feminine_firstname_factories: Dict[str, Callable[..., str]] = {}
    _neutral_firstname_factories: Dict[str, Callable[..., str]] = {}
    _surnames_factories: Dict[str, Callable[..., str]] = {}

    def __init__(self,
                 config: CharacterConfig,
                 name: CharacterName,
                 age: float,
                 max_age: float,
                 gender: Gender,
                 values: CharacterValues,
                 can_get_pregnant: bool = False) -> None:
        self.config = config
        self.name: CharacterName = name
        self.age: float = age
        self._max_age: float = max_age
        self.gender: Gender = gender
        self.can_get_pregnant: bool = can_get_pregnant
        self.location: Optional[int] = None
        self.location_aliases: Dict[str, int] = {}
        self.relationships: Dict[int, Relationship] = {}
        self.likes: Tuple[str, ...] = get_top_activities(values)
        self.values: CharacterValues = values

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(name={}, age={}/{}, gender={}, location={}, location_aliases={}, likes={}, relationships={}, {})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            round(self._max_age),
            self.gender,
            self.location,
            self.location_aliases,
            self.likes,
            len(self.relationships),
            str(self.values)
        )

    @classmethod
    def register_firstname_factory(cls, factory: Callable[..., str], name: str = "default", gender: Gender = Gender.NEUTRAL) -> None:
        """Adds a name factory function for use during character creation"""
        if gender == Gender.MASCULINE:
            cls._masculine_firstname_factories[name] = factory
        elif gender == Gender.FEMININE:
            cls._feminine_firstname_factories[name] = factory
        else:
            cls._neutral_firstname_factories[name] = factory

    @classmethod
    def register_surname_factory(cls, factory: Callable[..., str], name: str = "default") -> None:
        """Adds a name factory function for use during character creation"""
        cls._surnames_factories[name] = factory

    @classmethod
    def create(cls, config: CharacterConfig, **kwargs) -> 'GameCharacter':
        """Create a new instance of a character"""
        age: float = 0
        gender: Gender = random.choice(list(Gender))

        if gender == gender.MASCULINE:
            firstname = \
                cls._masculine_firstname_factories[config.masculine_names]()
        elif gender == gender.FEMININE:
            firstname = \
                cls._feminine_firstname_factories[config.feminine_names]()
        else:
            firstname = \
                cls._neutral_firstname_factories[config.neutral_names]()

        surname = cls._surnames_factories[config.surnames]()

        max_age: float = max(age + 1, np.random.normal(config.lifecycle.lifespan_mean,
                                                       config.lifecycle.lifespan_std))

        values = generate_character_values()

        return cls(
            config,
            CharacterName(firstname, surname),
            age,
            max_age,
            gender,
            values,
            can_get_pregnant=(gender == Gender.FEMININE)
        )


def generate_adult_age(config: CharacterConfig) -> float:
    return np.random.uniform(config.lifecycle.adult_age, config.lifecycle.adult_age + 15)
