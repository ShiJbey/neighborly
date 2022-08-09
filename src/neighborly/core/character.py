from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Type

from typing_extensions import TypedDict

from neighborly.core.ecs import Component, EntityArchetype, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.routine import Routine


class LifeStages(TypedDict):
    """Ages when characters are in certain stages of their lives"""

    child: int
    teen: int
    young_adult: int
    adult: int
    elder: int


@dataclass
class CharacterDefinition:
    """Configuration parameters for characters

    Fields
    ------
    lifecycle: LifeCycleConfig
        Configuration parameters for a characters lifecycle
    """

    _type_registry: ClassVar[Dict[str, CharacterDefinition]] = {}

    type_name: str
    life_stages: LifeStages
    lifespan: int
    chance_can_get_pregnant: float = 0.5

    @classmethod
    def register_type(cls, type_config: CharacterDefinition) -> None:
        """Registers a character config with the shared registry"""
        cls._type_registry[type_config.type_name] = type_config

    @classmethod
    def get_type(cls, name: str) -> CharacterDefinition:
        """Retrieve a CharacterConfig from the shared registry"""
        return cls._type_registry[name]


class CharacterName:
    __slots__ = "firstname", "surname"

    def __init__(self, firstname: str, surname: str) -> None:
        self.firstname: str = firstname
        self.surname: str = surname

    def __repr__(self) -> str:
        return f"{self.firstname} {self.surname}"

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"


class GameCharacter(Component):
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
    """

    __slots__ = (
        "character_def",
        "name",
        "age",
        "location",
        "location_aliases",
        "can_get_pregnant",
    )

    character_def_registry: Dict[str, CharacterDefinition] = {}

    def __init__(
        self,
        character_def: CharacterDefinition,
        name: CharacterName,
        age: float,
        can_get_pregnant: bool = False,
    ) -> None:
        super().__init__()
        self.character_def = character_def
        self.name: CharacterName = name
        self.age: float = age
        self.location: Optional[int] = None
        self.location_aliases: Dict[str, int] = {}
        self.can_get_pregnant: bool = can_get_pregnant

    def on_remove(self) -> None:
        if self.location:
            location = self.gameobject.world.get_gameobject(self.location)
            location.get_component(Location).remove_character(self.gameobject.id)
        self.location = None

    @classmethod
    def create(cls, world: World, **kwargs) -> GameCharacter:
        """Create a new instance of a character"""
        engine: NeighborlyEngine = world.get_resource(NeighborlyEngine)

        character_type_name = kwargs["character_type"]
        first_name, surname = kwargs.get(
            "name_format", "#first_name# #family_name#"
        ).split(" ")
        lifespan: int = kwargs["lifespan"]
        life_stages: LifeStages = kwargs["life_stages"]
        chance_can_get_pregnant: float = kwargs.get("chance_can_get_pregnant", 0.5)

        character_def = cls.get_character_def(
            CharacterDefinition(
                type_name=character_type_name,
                lifespan=lifespan,
                life_stages=life_stages,
            )
        )

        name = CharacterName(
            engine.name_generator.get_name(first_name),
            engine.name_generator.get_name(surname),
        )

        can_get_pregnant = engine.rng.random() < chance_can_get_pregnant

        # generate an age
        age = engine.rng.randint(
            character_def.life_stages["young_adult"],
            character_def.life_stages["elder"] - 1,
        )

        return GameCharacter(
            character_def=character_def,
            name=name,
            age=float(age),
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
            "can_get_pregnant": self.can_get_pregnant,
        }

    def __str__(self) -> str:
        return f"{str(self.name)}({self.gameobject.id})"

    def __repr__(self) -> str:
        """Return printable representation"""
        return "{}(name={}, age={}, location={}, location_aliases={}, can_get_pregnant={})".format(
            self.__class__.__name__,
            str(self.name),
            round(self.age),
            self.location,
            self.location_aliases,
            self.can_get_pregnant,
        )


class CharacterArchetype(EntityArchetype):
    """
    Archetype subclass for building characters
    """

    __slots__ = "name_format", "spawn_multiplier"

    def __init__(
        self,
        name: str,
        lifespan: int,
        life_stages: LifeStages,
        name_format: "#first_name# #family_name#",
        chance_can_get_pregnant: float = 0.5,
        spawn_multiplier: int = 1,
        extra_components: Dict[Type[Component], Dict[str, Any]] = None,
    ) -> None:
        super().__init__(name)
        self.name_format: str = name_format
        self.spawn_multiplier: int = spawn_multiplier

        self.add(
            GameCharacter,
            character_type=name,
            name_format=name_format,
            lifespan=lifespan,
            life_stages=life_stages,
            chance_can_get_pregnant=chance_can_get_pregnant,
        )

        self.add(Routine)
        self.add(PersonalValues)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class CharacterArchetypeLibrary:
    _registry: Dict[str, CharacterArchetype] = {}

    @classmethod
    def add(cls, archetype: CharacterArchetype, name: Optional[str] = None) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name if name else archetype.name] = archetype

    @classmethod
    def get_all(cls) -> List[CharacterArchetype]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> CharacterArchetype:
        """Get a LifeEventType using a name"""
        return cls._registry[name]
