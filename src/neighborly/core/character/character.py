from enum import Enum
from typing import Dict, NamedTuple, Optional, Tuple

from ordered_set import OrderedSet
from pydantic import BaseModel, Field

from neighborly.core.activity import get_top_activities
from neighborly.core.character.values import CharacterValues
from neighborly.core.ecs import Component


class LifeCycleConfig(BaseModel):
    """Configuration parameters for a characters lifecycle

    Fields
    ------
    can_age: bool
        Will his character's age change during th simulation
    can_die: bool
        Can this character die when it reaches it's max age
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

    name: str = Field(default="#first_name# #surname#")
    lifecycle: LifeCycleConfig = Field(default_factory=LifeCycleConfig)
    gender_overrides: Dict[str, "CharacterConfig"] = Field(default_factory=dict)


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

    def __init__(
            self,
            config: CharacterConfig,
            name: CharacterName,
            age: float,
            max_age: float,
            gender: Gender,
            values: CharacterValues,
            attracted_to: Tuple[Gender],
    ) -> None:
        super().__init__()
        self.config = config
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
