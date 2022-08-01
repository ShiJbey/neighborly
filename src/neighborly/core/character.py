from __future__ import annotations

import logging
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    NamedTuple,
    Optional,
    Tuple,
    TypedDict,
    Union,
)

from pydantic import BaseModel, Field, validator

from neighborly.core.ecs import Component, Event, IEventListener, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    EventCallbackDatabase,
    ILifeEventCallback,
    LifeEvent,
    LifeEventHandler,
)
from neighborly.core.utils.utilities import parse_number_range

logger = logging.getLogger(__name__)


class LifeStages(TypedDict):
    """Ages when characters are in certain stages of their lives"""

    child: int
    teen: int
    young_adult: int
    adult: int
    elder: int


class AgingConfig(BaseModel):
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
    num_children: Tuple[int, int]

    @validator("num_children", pre=True)
    def convert_age_ranges_to_tuples(cls, v):
        if isinstance(v, str):
            return parse_number_range(v)
        return v


class CharacterDefinition(BaseModel):
    """Configuration parameters for characters

    Fields
    ------
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    """

    _type_registry: ClassVar[Dict[str, CharacterDefinition]] = {}

    type_name: str
    first_name: str
    family_name: str
    aging: AgingConfig
    chance_can_get_pregnant: float = 0.5
    events: Dict[str, Dict[str, List[str]]] = Field(default_factory=dict)

    @classmethod
    def create(
        cls, options: Dict[str, Any], base: Optional[CharacterDefinition] = None
    ) -> CharacterDefinition:
        """Create a new Character type

        Parameters
        ----------
        options: Dict[str, Any]
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
        cls._type_registry[type_config.type_name] = type_config

    @classmethod
    def get_type(cls, name: str) -> CharacterDefinition:
        """Retrieve a CharacterConfig from the shared registry"""
        return cls._type_registry[name]


class CharacterName(NamedTuple):
    firstname: str
    surname: str

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class GameCharacter(Component, IEventListener):
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
    location_aliases: Dict[str, int]
        Maps string names to entity IDs of locations in the world
    _event_handlers: Dict[str, LifeEventHandler]
        Event handlers for the GameCharacter component
    """

    __slots__ = (
        "character_def",
        "name",
        "age",
        "location",
        "location_aliases",
        "can_get_pregnant",
        "_event_handlers",
    )

    character_def_registry: Dict[str, CharacterDefinition] = {}

    def __init__(
        self,
        character_def: CharacterDefinition,
        name: CharacterName,
        age: float,
        can_get_pregnant: bool = False,
        events: Optional[Dict[str, Dict[str, List[ILifeEventCallback]]]] = None,
    ) -> None:
        super().__init__()
        self.character_def = character_def
        self.name: CharacterName = name
        self.age: float = age
        self.location: Optional[int] = None
        self.location_aliases: Dict[str, int] = {}
        self.can_get_pregnant: bool = can_get_pregnant
        self._event_handlers: Dict[str, LifeEventHandler] = {}

        if events:
            for event_name, callbacks in events.items():
                preconditions = callbacks.get("preconditions", [])
                if event_name not in self._event_handlers:
                    self._event_handlers[event_name] = LifeEventHandler()

                for fn in preconditions:
                    self._event_handlers[event_name].add_precondition(fn)
                effects = callbacks.get("effects", [])
                for fn in effects:
                    self._event_handlers[event_name].add_effect(fn)

    @classmethod
    def create(cls, world: World, **kwargs) -> GameCharacter:
        """Create a new instance of a character"""
        engine: NeighborlyEngine = world.get_resource(NeighborlyEngine)

        character_def = cls.get_character_def(CharacterDefinition(**kwargs))

        name = CharacterName(
            engine.name_generator.get_name(character_def.first_name),
            engine.name_generator.get_name(character_def.family_name),
        )

        can_get_pregnant = engine.rng.random() < character_def.chance_can_get_pregnant

        # generate an age
        age_range: Optional[Union[str, tuple[int, int]]] = kwargs.get("age_range")

        if isinstance(age_range, str):
            lower_bound: int = character_def.aging.life_stages[age_range]  # type: ignore

            potential_upper_bounds = {
                "child": character_def.aging.life_stages["teen"],
                "teen": character_def.aging.life_stages["young_adult"],
                "young_adult": character_def.aging.life_stages["adult"],
                "adult": character_def.aging.life_stages["elder"],
                "elder": character_def.aging.lifespan,
            }

            age = engine.rng.randint(lower_bound, potential_upper_bounds[age_range] - 1)
        elif isinstance(age_range, tuple):
            age = engine.rng.randint(age_range[0], age_range[1])
        else:
            age = engine.rng.randint(
                character_def.aging.life_stages["young_adult"],
                character_def.aging.life_stages["adult"] - 1,
            )

        event_handlers: Dict[str, Dict[str, List[ILifeEventCallback]]] = {}

        for event_name, handler_config in character_def.events.items():
            if event_name not in event_handlers:
                event_handlers[event_name] = {"preconditions": [], "effects": []}

            for callback_name in handler_config.get("preconditions", []):
                event_handlers[event_name]["preconditions"].append(
                    EventCallbackDatabase.get_precondition(callback_name)
                )

            for callback_name in handler_config.get("effects", []):
                event_handlers[event_name]["effects"].append(
                    EventCallbackDatabase.get_effect(callback_name)
                )

        return GameCharacter(
            character_def=character_def,
            name=name,
            age=float(age),
            events=event_handlers,
            can_get_pregnant=can_get_pregnant,
        )

    @classmethod
    def get_character_def(
        cls, character_def: CharacterDefinition
    ) -> CharacterDefinition:
        """Returns an existing CharacterDefinition with the same name or creates a new one"""
        if character_def.type_name not in cls.character_def_registry:
            cls.character_def_registry[character_def.type_name] = character_def
        return cls.character_def_registry[character_def.type_name]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "character_def": self.character_def.type_name,
            "name": str(self.name),
            "age": self.age,
            "location": self.location,
            "location_aliases": self.location_aliases,
        }

    def will_handle_event(self, event: Event) -> bool:
        """
        Check the preconditions for this event type to see if they pass

        Returns
        -------
        bool
            True if the event passes all the preconditions
        """
        if event.get_type() in self._event_handlers and isinstance(event, LifeEvent):
            self._event_handlers[event.get_type()].check_preconditions(
                self.gameobject, event
            )

        return True

    def handle_event(self, event: LifeEvent) -> bool:
        """
        Perform logic when an event occurs

        Returns
        -------
        bool
            True if the event was handled successfully
        """
        if event.get_type() in self._event_handlers:
            self._event_handlers[event.get_type()].handle_event(self.gameobject, event)

        return True

    def on(
        self,
        event_type: str,
        precondition: Optional[ILifeEventCallback] = None,
        effect: Optional[ILifeEventCallback] = None,
    ) -> None:
        """Add new event callbacks for a given event type"""
        if precondition:
            self._event_handlers[event_type].preconditions.append(precondition)
        if effect:
            self._event_handlers[event_type].effects.append(effect)

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(name={}, age={}, location={}, location_aliases={})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            self.location,
            self.location_aliases,
        )
