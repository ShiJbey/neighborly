"""Neighborly Character Components

The module contains definitions of components used to compose Character entities.
It also contains definitions for common statuses and relationship statuses.

"""
from __future__ import annotations

import enum
import logging
import random
from abc import ABC, abstractmethod
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    final,
)

import attrs
import numpy as np
from numpy import typing as npt

from neighborly import Event
from neighborly.ai.brain import AIBrain, Goals
from neighborly.components.business import WorkHistory
from neighborly.components.shared import Age, FrequentedLocations, Lifespan
from neighborly.ecs import Component, GameObject, ISerializable, TagComponent, World
from neighborly.life_event import EventHistory
from neighborly.relationship import (
    Relationship,
    RelationshipCreatedEvent,
    Relationships,
    RomanticCompatibility,
)
from neighborly.roles import Roles
from neighborly.spawn_table import CharacterSpawnTable, CharacterSpawnTableEntry
from neighborly.stats import (
    ClampedStatComponent,
    StatComponent,
    StatModifier,
    StatModifierType,
    Stats,
)
from neighborly.statuses import IStatus, Statuses
from neighborly.tracery import Tracery
from neighborly.traits import ITrait, TraitLibrary, Traits

_logger = logging.getLogger(__name__)


class GameCharacter(Component, ISerializable):
    """Tags a GameObject as a character and tracks their name.

    Parameters
    ----------
    first_name
        The character's first name.
    last_name
        The character's last name or family name.
    """

    __slots__ = "first_name", "last_name", "_character_type"

    first_name: str
    """The character's first name."""

    last_name: str
    """The character's last name or family name."""

    _character_type: CharacterType
    """Reference to a component with character configuration data."""

    def __init__(
        self,
        first_name: str,
        last_name: str,
        character_type: CharacterType,
    ) -> None:
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self._character_type = character_type

    @property
    def character_type(self) -> CharacterType:
        return self._character_type

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "character_type": type(self.character_type).__name__,
        }

    def __repr__(self) -> str:
        return "{}(name={}, character_type={})".format(
            self.__class__.__name__, self.full_name, type(self.character_type).__name__
        )

    def __str__(self) -> str:
        return "{}(name={}, character_type={})".format(
            self.__class__.__name__, self.full_name, type(self.character_type).__name__
        )


@attrs.define
class LifeStageConfig:
    """A component that tracks configuration settings for aging."""

    adolescent_age: int
    """The age this species is considered an adolescent."""

    young_adult_age: int
    """The age this species is considered a young-adult."""

    adult_age: int
    """The age this species is considered an adult."""

    senior_age: int
    """The age this species is considered to be a senior."""


@attrs.define
class CharacterConfig:
    spawn_frequency: int = 1
    max_children_at_spawn: int = 0
    """The maximum number of children this character can spawn with."""
    avg_lifespan: Optional[int] = None
    max_health: int = 100
    base_health_decay: float = -2.5

    aging: Optional[LifeStageConfig] = None
    chance_spawn_with_spouse: float = 0
    """The probability of this character spawning with a spouse."""


class CharacterType(TagComponent, ABC):
    """Definition for a character that can be spawned into the world."""

    config: ClassVar[CharacterConfig] = CharacterConfig()

    @classmethod
    def on_register(cls, world: World) -> None:
        world.resource_manager.get_resource(CharacterSpawnTable).update(
            CharacterSpawnTableEntry(
                name=cls.__name__, spawn_frequency=cls.config.spawn_frequency
            )
        )

    @classmethod
    @abstractmethod
    def _instantiate(
        cls,
        world: World,
        **kwargs: Any,
    ) -> GameObject:
        """Creates a new character instance.

        Parameters
        ----------
        world
            The world to spawn the character into
        **kwargs
            Additional keyword arguments
        """
        raise NotImplementedError

    @classmethod
    @final
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        """Create a new GameObject instance of the given character type.

        Parameters
        ----------
        world
            The world to spawn the character into
        **kwargs
            Keyword arguments to pass to the CharacterType's factory

        Returns
        -------
        GameObject
            the instantiated character
        """
        character = cls._instantiate(world, **kwargs)

        CharacterCreatedEvent(world, character).dispatch()

        return character


class Health(ClampedStatComponent):
    """The amount of health a character has. characters die when this reaches zero."""

    def __init__(self, max_value: float) -> None:
        super().__init__(base_value=max_value, max_value=max_value, min_value=0)


class HealthDecay(StatComponent):
    """A potential amount of life lost by in adulthood characters after adolescence."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value)


class HealthDecayChance(ClampedStatComponent):
    """A potential amount of life lost by in adulthood characters after adolescence."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=1, min_value=0)


class Departed(IStatus):
    """Tags a character as departed from the simulation."""

    is_persistent = True


class CanGetPregnant(ITrait):
    """Tags a character as capable of getting pregnant and giving birth."""

    base_incidence = 0.5

    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        cls.incidence_modifiers.append(
            lambda gameobject: (
                StatModifier(-5000.0, StatModifierType.PercentAdd)
                if gameobject.has_component(CanGetOthersPregnant)
                else None
            )
        )

        cls.incidence_modifiers.append(
            lambda gameobject: (
                StatModifier(-500.0, StatModifierType.PercentAdd)
                if gameobject.has_component(Male)
                else None
            )
        )


class CanGetOthersPregnant(ITrait):
    """Tags a character as capable of getting other characters pregnant."""

    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        cls.incidence_modifiers.append(
            lambda gameobject: (
                StatModifier(-5000.0, StatModifierType.PercentAdd)
                if gameobject.has_component(CanGetPregnant)
                else None
            )
        )

        cls.incidence_modifiers.append(
            lambda gameobject: (
                StatModifier(-500.0, StatModifierType.PercentAdd)
                if gameobject.has_component(Female)
                else None
            )
        )


class Fertility(ClampedStatComponent):
    """Probability of this character having a child."""

    def __init__(self, base_value: float) -> None:
        super().__init__(base_value=base_value, max_value=1.0, min_value=0)


class FertilityDecay(StatComponent):
    """Reduction in fertility each year."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value)


class Deceased(IStatus):
    """Tags a character as deceased."""

    is_persistent = True


class Retired(IStatus):
    """Tags a character as retired."""

    is_persistent = True


class Virtue(enum.IntEnum):
    """An enumeration of virtue types."""

    ADVENTURE = 0
    AMBITION = enum.auto()
    EXCITEMENT = enum.auto()
    COMMERCE = enum.auto()
    CONFIDENCE = enum.auto()
    CURIOSITY = enum.auto()
    FAMILY = enum.auto()
    FRIENDSHIP = enum.auto()
    WEALTH = enum.auto()
    HEALTH = enum.auto()
    INDEPENDENCE = enum.auto()
    KNOWLEDGE = enum.auto()
    LEISURE_TIME = enum.auto()
    LOYALTY = enum.auto()
    LUST = enum.auto()
    MATERIAL_THINGS = enum.auto()
    NATURE = enum.auto()
    PEACE = enum.auto()
    POWER = enum.auto()
    RELIABILITY = enum.auto()
    ROMANCE = enum.auto()
    SINGLE_MINDEDNESS = enum.auto()
    SOCIALIZING = enum.auto()
    SELF_CONTROL = enum.auto()
    TRADITION = enum.auto()
    TRANQUILITY = enum.auto()


class Virtues(Component, ISerializable):
    """
    Values are what an entity believes in. They are used
    for decision-making and relationship compatibility among
    other things.


    Individual values are integers on the range [-50,50], inclusive.

    This model of entity values is borrowed from Dwarf Fortress'
    model of entity beliefs/values outlined at the following link
    https://dwarffortresswiki.org/index.php/DF2014:Personality_trait>.
    """

    VIRTUE_MAX: ClassVar[int] = 50
    """The maximum value an virtue can have."""

    VIRTUE_MIN: ClassVar[int] = -50
    """The minimum value a virtue can have."""

    STRONG_AGREE: ClassVar[int] = 35
    """The threshold for strong agreement with a virtue."""

    AGREE: ClassVar[int] = 25
    """The threshold for mild agreement with a virtue."""

    WEAK_AGREE: ClassVar[int] = 15
    """The threshold for weak agreement with a virtue."""

    WEAK_DISAGREE: ClassVar[int] = -15
    """The threshold for weak disagreement with a virtue."""

    DISAGREE: ClassVar[int] = -25
    """The threshold for mild disagreement with a virtue."""

    STRONG_DISAGREE: ClassVar[int] = -35
    """The threshold for strong disagreement with a virtue."""

    __slots__ = "_virtues"

    _virtues: npt.NDArray[np.int32]
    """An array representing the values of virtues."""

    def __init__(self, overrides: Optional[Dict[str, int]] = None) -> None:
        """
        Parameters
        ----------
        overrides
            Optionally override any virtue with a new value.
        """
        super().__init__()
        self._virtues = np.zeros(len(Virtue), dtype=np.int32)  # type: ignore

        if overrides:
            for trait, value in overrides.items():
                self[Virtue[trait]] = value

    def compatibility(self, other: Virtues) -> int:
        """Calculates the similarity between two Virtue components.

        Parameters
        ----------
        other
            The other set of virtues to compare to

        Returns
        -------
        int
            Similarity score on the range [-100, 100]


        Notes
        -----
        This method uses a combination of cosine similarity and similarity in magnitude
        to calculate the overall similarity of two sets of virtues.
        """
        # Cosine similarity is a value between -1 and 1
        norm_product: float = float(
            np.linalg.norm(self._virtues)
            * np.linalg.norm(other._virtues)
            # type: ignore
        )

        if norm_product == 0:
            cosine_similarity = 0.0
        else:
            cosine_similarity = float(
                np.dot(self._virtues, other._virtues) / norm_product
            )  # type: ignore

        # This the maximum difference in the magnitudes of the virtue vectors
        max_distance = 509.9019513592785
        distance = float(np.linalg.norm(self._virtues - other._virtues))  # type: ignore

        # Distance similarity is a value between -1 and 1
        distance_similarity = 2.0 * (1.0 - (distance / max_distance)) - 1.0

        similarity: int = round(100 * ((cosine_similarity + distance_similarity) / 2.0))

        return similarity

    def get_high_values(self, n: int = 3) -> List[Virtue]:
        """Return the virtues with n-highest values.

        Returns
        -------
        List[Virtue]
            A list of virtues.
        """
        sorted_index_array = np.argsort(self._virtues)[-n:]  # type: ignore

        value_names = list(Virtue)

        return [value_names[i] for i in sorted_index_array]

    def get_low_values(self, n: int = 3) -> List[Virtue]:
        """Return the virtues with the n-lowest values.

        Returns
        -------
        List[Virtue]
            A list of virtues.
        """
        sorted_index_array = np.argsort(self._virtues)[:n]  # type: ignore

        value_names = list(Virtue)

        return [value_names[i] for i in sorted_index_array]

    def __getitem__(self, item: Virtue) -> int:
        return int(self._virtues[item])

    def __setitem__(self, item: Virtue, value: int) -> None:
        self._virtues[item] = max(Virtues.VIRTUE_MIN, min(Virtues.VIRTUE_MAX, value))

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            {
                virtue.name: int(self._virtues[i])
                for i, virtue in enumerate(list(Virtue))
            },
        )

    def __iter__(self) -> Iterator[Tuple[Virtue, int]]:
        virtue_dict = {
            virtue: int(self._virtues[i]) for i, virtue in enumerate(list(Virtue))
        }

        return virtue_dict.items().__iter__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            virtue.name: int(self._virtues[i]) for i, virtue in enumerate(list(Virtue))
        }

    @staticmethod
    def factory(
        world: World,
        **kwargs: Any,
    ) -> Virtues:
        """Generate a new set of character values"""
        n_likes: int = kwargs.get("n_likes", 3)
        n_dislikes: int = kwargs.get("n_dislikes", 3)
        initialization: str = kwargs.get("initialization", "random")
        overrides: Dict[str, int] = kwargs.get("overrides", {})
        values_overrides: Dict[str, int] = {}

        if initialization == "zeros":
            pass

        elif initialization == "random":
            rng = world.resource_manager.get_resource(random.Random)

            for v in sorted(list(Virtue)):
                values_overrides[v.name] = rng.randint(-30, 30)

            # Select virtues types
            total_virtues: int = n_likes + n_dislikes
            chosen_virtues = rng.sample(list(Virtue), total_virtues)

            # select likes and dislikes
            high_values = sorted(rng.sample(chosen_virtues, n_likes))
            low_values = sorted(list(set(chosen_virtues) - set(high_values)))

            # Generate values for each ([30,50] for high values, [-50,-30] for dislikes)
            for trait in high_values:
                values_overrides[trait.name] = rng.randint(30, 50)

            for trait in low_values:
                values_overrides[trait.name] = rng.randint(-50, -30)
        else:
            # Using an unknown virtue doesn't break anything, but we should log it
            _logger.warning(f"Unrecognized Virtues initialization '{initialization}'")

        # Override any values with manually-specified values
        values_overrides = {**values_overrides, **overrides}

        return Virtues(values_overrides)


class Pregnant(IStatus):
    """Tags a character as pregnant and tracks relevant information."""

    __slots__ = "_partner"

    _partner: GameObject
    """The GameObject ID of the character that impregnated this character."""

    def __init__(self, year_created: int, partner: GameObject) -> None:
        super().__init__(year_created)
        self._partner = partner

    @property
    def partner(self) -> GameObject:
        return self._partner

    def __str__(self) -> str:
        return f"{type(self).__name__}(partner={self.partner.name})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(partner={self.partner.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "partner": self.partner.uid,
        }


class Family(IStatus):
    """Tags the relationship owner as a member of the target's family."""

    pass


class ParentOf(IStatus):
    """Tags the relationship owner as the parent of the target."""

    pass


class ChildOf(IStatus):
    """Tags the relationship owner as the child of the target."""

    pass


class SiblingOf(IStatus):
    """Tags the relationship owner as a sibling of the target."""

    pass


class Married(IStatus):
    """Tags two characters as being married"""

    pass


class Dating(IStatus):
    """Tags two characters as dating"""

    pass


class Gender(Component, ISerializable):
    """A component that tracks a character's gender expression."""

    __slots__ = "_gender_type"

    _gender_type: GenderType
    """The character's current gender."""

    def __init__(self, gender_type: GenderType) -> None:
        """
        Parameters
        ----------
        gender_type
            The character's current gender.
        """
        super().__init__()
        self._gender_type = gender_type

    @property
    def gender_type(self) -> GenderType:
        return self._gender_type

    def __str__(self) -> str:
        return f"{type(self).__name__}({type(self.gender_type).__name__})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({type(self.gender_type).__name__})"

    def to_dict(self) -> Dict[str, Any]:
        return {"gender": {type(self.gender_type).__name__}}


class GenderType(TagComponent, ABC):
    def on_add(self) -> None:
        if gender := self.gameobject.try_component(Gender):
            self.gameobject.remove_component(type(gender.gender_type))
            self.gameobject.remove_component(Gender)
        self.gameobject.add_component(Gender, gender_type=self)


class Male(GenderType):
    pass


class Female(GenderType):
    pass


class NonBinary(GenderType):
    pass


class SexualOrientation(ITrait, ABC):
    base_incidence = 0.5

    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        cls.incidence_modifiers.append(
            lambda gameobject: (
                StatModifier(-5000, StatModifierType.PercentAdd)
                if SexualOrientation.has_sexual_orientation(gameobject)
                else None
            )
        )

    @staticmethod
    def has_sexual_orientation(gameobject: GameObject) -> bool:
        return (
            len(
                [
                    c_type
                    for c_type in gameobject.get_component_types()
                    if issubclass(c_type, SexualOrientation)
                ]
            )
            > 0
        )


class Homosexual(ITrait):
    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        world.event_manager.on_event(
            RelationshipCreatedEvent, Homosexual.add_attraction_buff
        )

    @staticmethod
    def add_attraction_buff(event: RelationshipCreatedEvent) -> None:
        if event.owner.has_component(Homosexual):
            if isinstance(
                event.owner.get_component(Gender).gender_type,
                type(event.target.get_component(Gender).gender_type),
            ):
                event.relationship.get_component(RomanticCompatibility).add_modifier(
                    StatModifier(4, StatModifierType.Flat)
                )

            if not isinstance(
                event.owner.get_component(Gender).gender_type,
                type(event.target.get_component(Gender).gender_type),
            ):
                event.relationship.get_component(RomanticCompatibility).add_modifier(
                    StatModifier(-4, StatModifierType.Flat)
                )


class Heterosexual(ITrait):
    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        world.event_manager.on_event(
            RelationshipCreatedEvent, Heterosexual.add_attraction_buff
        )

    @staticmethod
    def add_attraction_buff(event: RelationshipCreatedEvent) -> None:
        if event.owner.has_component(Heterosexual):
            if isinstance(
                event.owner.get_component(Gender).gender_type,
                type(event.target.get_component(Gender).gender_type),
            ):
                event.relationship.get_component(RomanticCompatibility).add_modifier(
                    StatModifier(-4, StatModifierType.Flat)
                )

            if not isinstance(
                event.owner.get_component(Gender).gender_type,
                type(event.target.get_component(Gender).gender_type),
            ):
                event.relationship.get_component(RomanticCompatibility).add_modifier(
                    StatModifier(4, StatModifierType.Flat)
                )


class Asexual(ITrait):
    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        world.event_manager.on_event(
            RelationshipCreatedEvent, Asexual.add_attraction_buff
        )

    @staticmethod
    def add_attraction_buff(event: RelationshipCreatedEvent) -> None:
        if event.owner.has_component(Asexual):
            event.relationship.get_component(RomanticCompatibility).add_modifier(
                StatModifier(-10, StatModifierType.Flat)
            )


class Boldness(ClampedStatComponent):
    """A measure of a character's ambitiousness."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class Compassion(ClampedStatComponent):
    """A measure of how compassionate character is."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class Greed(ClampedStatComponent):
    """A measure of how greedy a character is."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class Honor(ClampedStatComponent):
    """A measure of how honorable a character is."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class Sociability(ClampedStatComponent):
    """A measure of how socially-inclined or extroverted a character is."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class Vengefulness(ClampedStatComponent):
    """A measure of how much a character holds grudges."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class Attractiveness(ClampedStatComponent):
    """Tracks how visually attractive a character is."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=255, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.randint(0, 255)))
        return cls(base_value=base_value)


class SocialInfluence(ClampedStatComponent):
    """A measure of how honorable a character is."""

    def __init__(self, base_value: float = 0) -> None:
        super().__init__(base_value=base_value, max_value=10, min_value=0)

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any):
        base_value = kwargs.get("base_value", 0)
        return cls(base_value=base_value)


class LifeStageType(enum.IntEnum):
    """An enumeration of all the various life stages aging characters pass through."""

    Child = 0
    Adolescent = enum.auto()
    YoungAdult = enum.auto()
    Adult = enum.auto()
    Senior = enum.auto()


class LifeStage(Component, ISerializable):
    """A component that tracks the current life stage of a character."""

    __slots__ = "life_stage"

    life_stage: LifeStageType
    """The character's current life stage."""

    def __init__(self, life_stage: Union[str, LifeStageType] = "Child") -> None:
        """
        Parameters
        ----------
        life_stage
            The character's current life stage.
        """
        super().__init__()
        self.life_stage = (
            life_stage
            if isinstance(life_stage, LifeStageType)
            else LifeStageType[life_stage]
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.life_stage.name})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.life_stage.name})"

    def to_dict(self) -> Dict[str, Any]:
        return {"life_stage": self.life_stage.name}


class CanAge(ITrait):
    """Tags a GameObject as being able to change life stages as time passes."""

    pass


class Immortal(ITrait):
    base_incidence = 0.0

    def on_add(self) -> None:
        self.gameobject.get_component(HealthDecay).add_modifier(
            StatModifier(-5000.0, StatModifierType.PercentAdd, source=self)
        )

    def on_remove(self) -> None:
        self.gameobject.get_component(HealthDecay).remove_modifiers_from_source(self)

    @classmethod
    def on_register(cls, world: World) -> None:
        super().on_register(world)
        cls.incidence_modifiers.append(Immortal.both_parents_have_trait)

    @staticmethod
    def both_parents_have_trait(gameobject: GameObject) -> StatModifier:
        parents = [
            relationship.get_component(Relationship).target
            for relationship in gameobject.get_component(
                Relationships
            ).get_relationships_with_components(ChildOf)
        ]

        parents_with_trait = [
            parent for parent in parents if parent.has_component(Immortal)
        ]

        if len(parents_with_trait) >= 2:
            return StatModifier(50, StatModifierType.PercentAdd)
        else:
            return StatModifier(0, StatModifierType.PercentAdd)


class BaseCharacter(CharacterType):
    base_components: ClassVar[Dict[Union[str, Type[Component]], Dict[str, Any]]] = {}

    @classmethod
    def add_default_component(
        cls, component_type: Type[Component], **kwargs: Any
    ) -> None:
        """Add a new component to the default set of component all characters have.

        Parameters
        ----------
        component_type
            The class of the component
        **kwargs
            Keyword arguments to pass to the component's factory
        """
        cls.base_components[component_type] = {**kwargs}

    @classmethod
    def _add_traits(cls, gameobject: GameObject) -> None:
        """Adds incidental traits to the character GameObject."""
        rng = gameobject.world.resource_manager.get_resource(random.Random)
        trait_library = gameobject.world.resource_manager.get_resource(TraitLibrary)

        for trait_type in trait_library:
            if rng.random() <= trait_type.get_incidence(gameobject):
                gameobject.add_component(trait_type)

    @classmethod
    def _generate_character_name(
        cls, character: GameObject, first_name: str = "", last_name: str = ""
    ) -> Tuple[str, str]:
        """Overwrite a characters first or last name.

        Parameters
        ----------
        character
            The character to modify
        first_name
            An optional override for the first name
        last_name
            An optional override for the last name
        """
        tracery = character.world.resource_manager.get_resource(Tracery)
        gender = type(character.get_component(Gender).gender_type).__name__

        generated_first_name = (
            first_name
            if first_name
            else tracery.generate(f"#character::first_name::{gender}#")
        )

        generated_last_name = (
            last_name if last_name else tracery.generate("#character::last_name#")
        )

        return generated_first_name, generated_last_name

    @classmethod
    def _set_character_age(
        cls,
        character: GameObject,
        new_age: int,
    ) -> None:
        age = character.get_component(Age)
        age.value = new_age

        aging_config = cls.config.aging

        if aging_config is None:
            return None

        life_stage = character.get_component(LifeStage)

        if age.value >= aging_config.senior_age:
            life_stage.life_stage = LifeStageType.Senior

        elif age.value >= aging_config.adult_age:
            life_stage.life_stage = LifeStageType.Adult

        elif age.value >= aging_config.young_adult_age:
            life_stage.life_stage = LifeStageType.YoungAdult

        elif age.value >= aging_config.adolescent_age:
            life_stage.life_stage = LifeStageType.Adolescent

        else:
            life_stage.life_stage = LifeStageType.Child

    @classmethod
    def _set_life_stage(
        cls, character: GameObject, life_stage_type: LifeStageType
    ) -> None:
        """Overwrites the current LifeStage and age of a character.

        Parameters
        ----------
        character
            The character to modify
        life_stage_type
            The life stage to update to
        """
        age = character.get_component(Age)

        aging_config = cls.config.aging

        if aging_config is None:
            return None

        character.get_component(LifeStage).life_stage = life_stage_type

        if life_stage_type == LifeStageType.Senior:
            age.value = aging_config.senior_age

        elif life_stage_type == LifeStageType.Adult:
            age.value = aging_config.adult_age

        elif life_stage_type == LifeStageType.YoungAdult:
            age.value = aging_config.young_adult_age

        elif life_stage_type == LifeStageType.Adolescent:
            age.value = aging_config.adolescent_age

        elif life_stage_type == LifeStageType.Child:
            age.value = 0

    @classmethod
    def _generate_age_from_life_stage(
        cls,
        rng: random.Random,
        aging_config: LifeStageConfig,
        life_stage_type: LifeStageType,
    ) -> int:
        """Return an age for the character given their life_stage"""
        if life_stage_type == LifeStageType.Child:
            return rng.randint(0, aging_config.adolescent_age - 1)
        elif life_stage_type == LifeStageType.Adolescent:
            return rng.randint(
                aging_config.adolescent_age,
                aging_config.young_adult_age - 1,
            )
        elif life_stage_type == LifeStageType.YoungAdult:
            return rng.randint(
                aging_config.young_adult_age,
                aging_config.adult_age - 1,
            )
        elif life_stage_type == LifeStageType.Adult:
            return rng.randint(
                aging_config.adult_age,
                aging_config.senior_age - 1,
            )
        else:
            return aging_config.senior_age + int(10 * rng.random())

    @classmethod
    def _instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        first_name: str = kwargs.get("first_name", "")
        last_name: str = kwargs.get("last_name", "")
        age: Optional[int] = kwargs.get("age")
        life_stage: Optional[LifeStageType] = kwargs.get("life_stage")
        gender: Optional[Type[GenderType]] = kwargs.get("gender")
        rng = world.resource_manager.get_resource(random.Random)

        character = world.gameobject_manager.spawn_gameobject(
            components={
                Traits: {},
                Statuses: {},
                Stats: {},
                Roles: {},
                Relationships: {},
                Virtues: {},
                FrequentedLocations: {},
                AIBrain: {},
                Goals: {},
                EventHistory: {},
                Age: {"value": 0},
                LifeStage: {},
                WorkHistory: {},
                Health: {"max_value": cls.config.max_health},
                HealthDecay: {"base_value": 0.0},
                HealthDecayChance: {"base_value": 0.0},
                Boldness: {"base_value": rng.randint(0, 255)},
                Compassion: {"base_value": rng.randint(0, 255)},
                Greed: {"base_value": rng.randint(0, 255)},
                Honor: {"base_value": rng.randint(0, 255)},
                Sociability: {"base_value": rng.randint(0, 255)},
                Vengefulness: {"base_value": rng.randint(0, 255)},
                Attractiveness: {"base_value": rng.randint(0, 255)},
                Fertility: {"base_value": 0},
                FertilityDecay: {"base_value": 0},
                **BaseCharacter.base_components,
                cls: {},
            }
        )

        if lifespan_value := cls.config.avg_lifespan:
            character.add_component(Lifespan, value=lifespan_value)

        # Fix inconsistencies and override values
        if life_stage is not None:
            cls._set_life_stage(character=character, life_stage_type=life_stage)

        if age is not None:
            cls._set_character_age(character=character, new_age=age)

        if gender is not None:
            character.add_component(gender)
        else:
            rng = world.resource_manager.get_resource(random.Random)
            gender = rng.choice((Male, Female, NonBinary))
            character.add_component(gender)

        cls._add_traits(character)

        first_name, last_name = cls._generate_character_name(
            character, first_name=first_name, last_name=last_name
        )

        character.add_component(
            GameCharacter,
            first_name=first_name,
            last_name=last_name,
            character_type=character.get_component(cls),
        )

        character.name = (
            f"{character.get_component(GameCharacter).full_name}({character.uid})"
        )

        return character


class CharacterCreatedEvent(Event):
    __slots__ = "_character"

    def __init__(
        self,
        world: World,
        character: GameObject,
    ) -> None:
        super().__init__(world)
        self._character = character

    @property
    def character(self) -> GameObject:
        return self._character
