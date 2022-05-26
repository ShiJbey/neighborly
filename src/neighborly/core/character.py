from __future__ import annotations
from collections import defaultdict

from typing import Any, ClassVar, NamedTuple, Optional, TypedDict, Union

from pydantic import BaseModel, Field, validator

from neighborly.core import name_generation as name_gen
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentDefinition
from neighborly.core.rng import IRandNumGenerator
from neighborly.core.tags import Tag
from neighborly.core.life_event import (
    LifeEvent,
    ILifeEventCallback,
    LifeEventHandler,
    ILifeEventListener,
)
from neighborly.core.utils.utilities import parse_number_range


class LifeStages(TypedDict):
    """Ages when characters are in certain stages of their lives"""

    child: int
    teen: int
    young_adult: int
    adult: int
    elder: int


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

    life_stages: LifeStages
    lifespan: int


class FamilyGenerationOptions(BaseModel):
    """Options used when generating a family for a new character entering the town"""

    probability_spouse: float
    probability_children: float
    num_children: tuple[int, int]

    @validator("num_children", pre=True)
    def convert_age_ranges_to_tuples(cls, v):
        if isinstance(v, str):
            return parse_number_range(v)
        return v


class GenerationConfig(BaseModel):
    """Parameters for generating new characters with this type"""

    first_name: str
    last_name: str
    family: FamilyGenerationOptions
    gender_weights: dict[str, int] = Field(default_factory=dict)


class CharacterDefinition(BaseModel):
    """Configuration parameters for characters

    Fields
    ------
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    """

    _type_registry: ClassVar[dict[str, CharacterDefinition]] = {}

    name: str
    lifecycle: LifeCycleConfig
    generation: GenerationConfig
    gender_overrides: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls, options: dict[str, Any], base: Optional[CharacterDefinition] = None
    ) -> CharacterDefinition:
        """Create a new Character type

        Parameters
        ----------
        options: dict[str, Any]
            data used to instantiate the CharacterType
        base: CharacterType
            Character type to base the new type off of
        """

        character_def = {}

        if base:
            character_def.update(base.dict())

        character_def.update(options)

        return CharacterDefinition(**character_def)

    @classmethod
    def register_type(cls, type_config: CharacterDefinition) -> None:
        """Registers a character config with the shared registry"""
        cls._type_registry[type_config.name] = type_config

    @classmethod
    def get_type(cls, name: str) -> CharacterDefinition:
        """Retrieve a CharacterConfig from the shared registry"""
        return cls._type_registry[name]


class CharacterName(NamedTuple):
    firstname: str
    surname: str

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class GameCharacter(Component, ILifeEventListener):
    """
    The state of a single character within the world

    Attributes
    ----------
    character_def: CharacterType
        Configuration settings for the character
    name: CharacterName
        The character's name
    age: float
        The character's current age in years
    location: int
        Entity ID of the location where this character current is
    location_aliases: dict[str, int]
        Maps string names to entity IDs of locations in the world
    tags: dict[str, Tag]
        Tags attached to this character
    _event_handlers: dict[str, LifeEventHandler]
        Event handlers for the GameCharacter component
    """

    __slots__ = (
        "character_def",
        "name",
        "age",
        "location",
        "location_aliases",
        "tags",
        "_event_handlers",
    )

    def __init__(
        self,
        character_def: CharacterDefinition,
        name: CharacterName,
        age: float,
        tags: Optional[list[Tag]] = None,
        events: Optional[dict[str, dict[str, list[ILifeEventCallback]]]] = None,
    ) -> None:
        super().__init__()
        self.character_def = character_def
        self.name: CharacterName = name
        self.age: float = age
        self.location: Optional[int] = None
        self.location_aliases: dict[str, int] = {}
        self.tags: dict[str, Tag] = {}
        self._event_handlers: defaultdict[str, LifeEventHandler] = defaultdict(
            LifeEventHandler
        )

        if tags:
            self.tags.update({tag.name: tag for tag in tags})

        if events:
            for event_name, callbacks in events.items():
                preconditions = callbacks.get("preconditions", [])
                for fn in preconditions:
                    self._event_handlers[event_name].add_precondition(fn)
                effects = callbacks.get("effects", [])
                for fn in effects:
                    self._event_handlers[event_name].add_effect(fn)

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character_def": self.character_def.name,
            "name": str(self.name),
            "age": self.age,
            "location": self.location,
            "location_aliases": self.location_aliases,
            "tags": list(self.tags.keys()),
        }

    def check_preconditions(self, event: LifeEvent) -> bool:
        """
        Check the preconditions for this event type to see if they pass

        Returns
        -------
        bool
            True if the event passes all the preconditions
        """
        self._event_handlers[event.event_type].check_preconditions(
            self.gameobject, event
        )

        if self.tags:
            for tag in self.tags.values():
                precondition = tag.event_preconditions.get(event.event_type)
                if (
                    precondition is not None
                    and precondition(self.gameobject, event) is False
                ):
                    return False
        return True

    def handle_event(self, event: LifeEvent) -> bool:
        """
        Perform logic when an event occurs

        Returns
        -------
        bool
            True if the event was handled successfully
        """
        self._event_handlers[event.event_type].handle_event(self.gameobject, event)

        for tag in self.tags.values():
            effect = tag.event_effects.get(event.event_type)
            if effect is not None and effect(self.gameobject, event) is False:
                return False
        return True

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(name={}, age={}, location={}, location_aliases={})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            self.location,
            self.location_aliases,
        )


def generate_character(
    character_def: CharacterDefinition, rng: IRandNumGenerator, **kwargs
) -> GameCharacter:
    first_name = kwargs.get(
        "first_name", name_gen.get_name(character_def.generation.first_name)
    )
    last_name = kwargs.get(
        "last_name", name_gen.get_name(character_def.generation.last_name)
    )
    name = CharacterName(first_name, last_name)

    # generate an age
    age_range: Optional[Union[str, tuple[int, int]]] = kwargs.get("age_range")

    if isinstance(age_range, str):
        lower_bound: int = character_def.lifecycle.life_stages[age_range]

        potential_upper_bounds = {
            "child": character_def.lifecycle.life_stages["teen"],
            "teen": character_def.lifecycle.life_stages["young_adult"],
            "young_adult": character_def.lifecycle.life_stages["adult"],
            "adult": character_def.lifecycle.life_stages["elder"],
            "elder": character_def.lifecycle.lifespan,
        }

        age = rng.randint(lower_bound, potential_upper_bounds[age_range] - 1)
    elif isinstance(age_range, tuple):
        age = rng.randint(age_range[0], age_range[1])
    else:
        age = rng.randint(
            character_def.lifecycle.life_stages["young_adult"],
            character_def.lifecycle.life_stages["adult"] - 1,
        )

    return GameCharacter(
        character_def=character_def,
        name=name,
        age=float(age),
    )


class GameCharacterFactory(AbstractFactory):
    """
    Default factory for constructing instances of GameCharacters.
    """

    def __init__(self) -> None:
        super().__init__("GameCharacter")

    def create(self, spec: ComponentDefinition, **kwargs) -> GameCharacter:
        """Create a new instance of a character"""
        return generate_character(
            character_def=CharacterDefinition.get_type(spec["character_def"]), **kwargs
        )
