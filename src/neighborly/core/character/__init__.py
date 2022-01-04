import random
from pathlib import Path
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from neighborly.core.relationship import Relationship

AnyPath = Union[str, Path]


@dataclass(frozen=True)
class LifeCycleConfig:
    lifespan_mean: int = 85
    lifespan_std: int = 15
    adult_age: int = 18


@dataclass(frozen=True)
class CharacterConfig:
    masculine_names: str = 'default'
    feminine_names: str = 'default'
    lifecycle: LifeCycleConfig = field(default_factory=LifeCycleConfig)
    components: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class CharacterName(NamedTuple):
    firstname: str
    surname: str

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class DefaultCharacterNameFactory:
    """Loads names from text files and creates character names"""

    __slots__ = "first_names", "surnames"

    def __init__(self, firstname_file: AnyPath, surname_file: AnyPath) -> None:
        with open(firstname_file, 'r') as f:
            self.first_names: List[str] = f.read().splitlines()
        with open(surname_file, 'r') as f:
            self.surnames: List[str] = f.read().splitlines()

    def __call__(self) -> CharacterName:
        return CharacterName(
            random.choice(self.first_names),
            random.choice(self.surnames)
        )


class Gender(Enum):
    MASCULINE = 0
    FEMININE = 1


class GameCharacter:
    """The state of a single character within the world"""

    __slots__ = "config", "name", "age", "_max_age", "gender", "can_get_pregnant", \
        "location", "location_aliases", "relationships"

    _masculine_names: Dict[str, Callable[..., CharacterName]] = {}
    _feminine_names: Dict[str, Callable[..., CharacterName]] = {}

    def __init__(self,
                 config: CharacterConfig,
                 name: CharacterName,
                 age: float,
                 max_age: float,
                 gender: Gender,
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

    def __repr__(self) -> str:
        return "{}(name={}, age={}, gender={}, location={}, location_aliases={})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            self.gender,
            self.location,
            self.location_aliases
        )

    @classmethod
    def register_name_factory(cls, is_masculine: bool, name: str, factory: Callable[..., CharacterName]) -> None:
        if is_masculine:
            cls._masculine_names[name] = factory
        else:
            cls._feminine_names[name] = factory

    @classmethod
    def create(cls, config: CharacterConfig, **kwargs) -> 'GameCharacter':
        """Create a new instance of a character"""
        age: float = 0
        gender: Gender = random.choice(list(Gender))

        if gender == gender.MASCULINE:
            name = cls._masculine_names[config.masculine_names]()
        else:
            name = cls._feminine_names[config.feminine_names]()

        max_age: float = max(age + 1, np.random.normal(config.lifecycle.lifespan_mean,
                                                       config.lifecycle.lifespan_std))

        return cls(
            config,
            name,
            age,
            max_age,
            gender,
            can_get_pregnant=gender == Gender.FEMININE
        )


def generate_adult_age(config: CharacterConfig) -> float:
    return np.random.uniform(config.lifecycle.adult_age, config.lifecycle.adult_age + 15)
