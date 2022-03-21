import random
from enum import Enum
from typing import Dict, NamedTuple, Optional, Tuple, List

import numpy as np
from ordered_set import OrderedSet
from pydantic import BaseModel, Field

from neighborly.core import name_generation as name_gen
from neighborly.core.activity import _activity_registry
from neighborly.core.character.values import CharacterValues, generate_character_values
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


class LifeCycleConfig(BaseModel):
    """Configuration parameters for a characters lifecycle

    Fields
    ------
    can_age: bool
        Will his character's age change during th simulation
    can_die: bool
        Can this character die when it reaches its max age
    lifespan_mean: int
        Average lifespan of characters with this configuration
    lifespan_std: int
        Standard deviation of the lifespans of characters with this
        configuration
    adult_age: int
        Age that characters with thi config are considered adults
        in society
    romantic_feelings_age: int
        The age that characters start to develop romantic feelings
        for other characters
    """

    can_age: bool = True
    can_die: bool = True
    lifespan_mean: int = 85
    lifespan_std: int = 15
    adult_age: int = 18
    senior_age: int = 65
    romantic_feelings_age: int = 13
    marriageable_age: int = 18


class CharacterConfig(BaseModel):
    """Configuration parameters for characters

    Fields
    ------
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    """
    config_name: str
    name: str = Field(default="#first_name# #surname#")
    lifecycle: LifeCycleConfig = Field(default_factory=LifeCycleConfig)
    gender_overrides: Dict[str, "CharacterConfig"] = Field(
        default_factory=dict)


class CharacterName(NamedTuple):
    firstname: str
    surname: str

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class Gender(Enum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTRAL = "neutral"


class GameCharacter(Component):
    """The state of a single character within the world

    Attributes
    ----------
    config: CharacterConfig
        Configuration settings for the character
    name: CharacterName
        The character's name
    age: float
        The character's current age in years
    max_age: float
        The age that this character is going to die of natural causes
    gender: Gender
        Loose gender identity for the character
    location: int
        Entity ID of the location where this character current is
    location_aliases: Dict[str, int]
        Maps string names to entity IDs of locations in the world
    likes: Tuple[str, ...]
        Names of activities that this character likes to do
    values: CharacterValues
        A characters beliefs/values in life (i.e. loyalty, family, wealth)
    """

    __slots__ = (
        "config",
        "alive",
        "name",
        "age",
        "max_age",
        "gender",
        "can_get_pregnant",
        "location",
        "location_aliases",
        "values",
        "likes",
        "attracted_to"
    )

    _config_registry: Dict[str, CharacterConfig] = {}

    def __init__(
            self,
            config: CharacterConfig,
            name: CharacterName,
            age: float,
            max_age: float,
            gender: Gender,
            values: CharacterValues,
            attracted_to: Tuple[Gender, ...],
    ) -> None:
        super().__init__()
        self.config = config
        self.alive: bool = True
        self.name: CharacterName = name
        self.age: float = age
        self.max_age: float = max_age
        self.gender: Gender = gender
        self.attracted_to: OrderedSet[Gender] = OrderedSet(attracted_to)
        self.location: Optional[int] = None
        self.location_aliases: Dict[str, int] = {}
        self.likes: Tuple[str, ...] = get_top_activities(values)
        self.values: CharacterValues = values

    def on_start(self) -> None:
        self.gameobject.set_name(str(self.name))

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(name={}, age={}/{}, gender={}, location={}, location_aliases={}, likes={}, {})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            round(self.max_age),
            self.gender,
            self.location,
            self.location_aliases,
            self.likes,
            str(self.values),
        )

    @classmethod
    def register_config(cls, name: str, config: CharacterConfig) -> None:
        """Registers a character config with the shared registry"""
        cls._config_registry[name] = config

    @classmethod
    def get_registered_config(cls, name: str) -> CharacterConfig:
        """Retrieve a CharacterConfig from the shared registry"""
        return cls._config_registry[name]


class GameCharacterFactory(AbstractFactory):
    """
    Default factory for constructing instances of
    GameCharacters.
    """

    def __init__(self) -> None:
        super().__init__("GameCharacter")

    def create(self, spec: ComponentSpec) -> GameCharacter:
        """Create a new instance of a character"""

        config: CharacterConfig = GameCharacter.get_registered_config(spec['config_name'])

        age_range: str = spec.get_attribute("age_range", "adult")
        age: float = 0

        if age_range == "child":
            age = float(random.randint(3, config.lifecycle.adult_age))
        elif age_range == "adult":
            age = float(
                random.randint(config.lifecycle.adult_age,
                               config.lifecycle.senior_age)
            )
        else:
            age = float(
                random.randint(
                    config.lifecycle.senior_age, config.lifecycle.lifespan_mean
                )
            )

        gender: Gender = random.choice(list(Gender))

        name_rule: str = (
            config.gender_overrides[str(gender)].name
            if str(gender) in config.gender_overrides
            else config.name
        )

        firstname, surname = tuple(name_gen.get_name(name_rule).split(" "))

        max_age: float = max(
            age + 1,
            np.random.normal(
                config.lifecycle.lifespan_mean, config.lifecycle.lifespan_std
            ),
        )

        values: CharacterValues = generate_character_values()

        character = GameCharacter(
            config,
            CharacterName(firstname, surname),
            age,
            max_age,
            gender,
            values,
            tuple(random.sample(list(Gender), random.randint(0, 2))),
        )

        return character

    @staticmethod
    def generate_adult_age(config: CharacterConfig) -> float:
        return np.random.uniform(
            config.lifecycle.adult_age, config.lifecycle.adult_age + 15
        )


def create_family(
        n_children: Optional[int] = None
) -> Dict[str, List[GameCharacter]]:
    adults: List[GameCharacter] = []
    children: List[GameCharacter] = []

    character = cls.create(config)

    adults.append(character)

    spouse_gender = random.choice(character.attracted_to)

    spouse = GameCharacter(
        name=GameCharacter.name_factories[config.name_generator](
            gender=spouse_gender, surname=character.name.surname),
        gender=spouse_gender,
        attracted_to=[character.gender],
        hometown=character.hometown,
        config=config,
        age=generate_age(),
    )

    adults.append(spouse)

    years_married = random.randint(
        1, int(min(character.age, spouse.age)) - 18)

    num_children = n_children if n_children else random.randint(0, 4)

    for _ in range(num_children):
        gender = choose_gender(config)
        child = GameCharacter(
            name=GameCharacter.name_factories[config.name_generator](
                gender=gender,
                surname=character.name.surname,
            ),
            gender=gender,
            attracted_to=choose_attraction(config),
            hometown=character.hometown,
            config=config,
            age=generate_age(age_min=0, age_max=years_married),
        )
        children.append(child)

    return {'adults': adults, 'children': children}


def get_top_activities(
        character_values: CharacterValues, n: int = 3
) -> Tuple[str, ...]:
    """Return the top activities a character would enjoy given their values"""

    scores: List[Tuple[int, str]] = []

    for name, activity in _activity_registry.items():
        score: int = int(np.dot(character_values.traits, activity.character_traits.traits))
        scores.append((score, name))

    return tuple(
        [
            activity_score[1]
            for activity_score in sorted(scores, key=lambda s: s[0], reverse=True)
        ][:n]
    )
