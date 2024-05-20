"""Content libraries.

All content that can be authored or configured using external data files is collected
in a library. This makes it easy to look up any authored content using its definition
ID.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Generic, Iterable, Optional, Protocol, Type, TypeVar

from ordered_set import OrderedSet

from neighborly.action import ActionConsideration
from neighborly.components.beliefs import Belief
from neighborly.components.business import JobRole
from neighborly.components.character import SpeciesType
from neighborly.components.location import LocationPreferenceRule
from neighborly.components.skills import Skill
from neighborly.components.traits import Trait
from neighborly.defs.base_types import (
    BeliefDef,
    BusinessDef,
    CharacterDef,
    ContentDefinition,
    DistrictDef,
    JobRoleDef,
    LocationPreferenceDef,
    SettlementDef,
    SkillDef,
    SpeciesDef,
    TraitDef,
)
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.helpers.content_selection import get_with_tags
from neighborly.preconditions.base_types import Precondition

_T = TypeVar("_T", bound=ContentDefinition)


class ContentDefinitionLibrary(Generic[_T]):
    """The collection of skill definitions and instances."""

    _slots__ = ("definitions",)

    definitions: dict[str, _T]
    """IDs mapped to definition instances."""

    def __init__(self) -> None:
        self.definitions = {}

    def get_definition(self, definition_id: str) -> _T:
        """Get a definition from the library."""

        return self.definitions[definition_id]

    def add_definition(self, definition: _T) -> None:
        """Add a definition to the library."""

        self.definitions[definition.definition_id] = definition

    def get_definition_with_tags(self, tags: list[str]) -> list[_T]:
        """Get a definition from the library with the given tags."""

        return get_with_tags(
            options=[(d, d.tags) for d in self.definitions.values()], tags=tags
        )


class SkillLibrary(ContentDefinitionLibrary[SkillDef]):
    """Manages skill definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, Skill]
    """Skill instances."""

    def __init__(self) -> None:
        super().__init__()
        self.instances = {}

    def add_skill(self, skill: Skill) -> None:
        """Add skill to the library."""
        self.instances[skill.definition_id] = skill

    def get_skill(self, definition_id: str) -> Skill:
        """Get a skill instance."""
        return self.instances[definition_id]


class TraitLibrary(ContentDefinitionLibrary[TraitDef]):
    """Manages trait definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, Trait]
    """Trait instances."""

    def __init__(self) -> None:
        super().__init__()
        self.instances = {}

    def add_trait(self, trait: Trait) -> None:
        """Add trait to the library."""
        self.instances[trait.definition_id] = trait

    def get_trait(self, definition_id: str) -> Trait:
        """Get a trait instance."""
        return self.instances[definition_id]


class SpeciesLibrary(ContentDefinitionLibrary[SpeciesDef]):
    """Manages species definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, SpeciesType]
    """Species instances."""

    def __init__(self) -> None:
        super().__init__()
        self.instances = {}

    def add_species(self, species: SpeciesType) -> None:
        """Add species to the library."""
        self.instances[species.definition_id] = species

    def get_species(self, definition_id: str) -> SpeciesType:
        """Get a species instance."""
        return self.instances[definition_id]


class IDistrictFactory(ABC):
    """Creates instances of district gameobjects using a single definition."""

    @abstractmethod
    def create_district(self, world: World, definition_id: str) -> GameObject:
        """Create instance of district from a district definition.

        Parameters
        ----------
        world
            The simulation's World instance.
        definition_id
            The ID of the district's definition.

        Returns
        -------
        GameObject
            The new district.
        """
        raise NotImplementedError()


class DistrictLibrary(ContentDefinitionLibrary[DistrictDef]):
    """A collection of all district definitions."""

    _slots__ = ("factory",)

    factory: IDistrictFactory
    """The factory used to create new district from definitions."""

    def __init__(self, factory: IDistrictFactory) -> None:
        super().__init__()
        self.factory = factory


class ISettlementFactory(ABC):
    """Creates instances of settlement gameobjects using a single definition."""

    @abstractmethod
    def create_settlement(self, world: World, definition_id: str) -> GameObject:
        """Create instance of settlement from a settlement definition.

        Parameters
        ----------
        world
            The simulation's World instance.
        definition_id
            The ID of the settlement's definition.

        Returns
        -------
        GameObject
            The new settlement.
        """
        raise NotImplementedError()


class SettlementLibrary(ContentDefinitionLibrary[SettlementDef]):
    """A Collection of all the settlement definitions."""

    _slots__ = ("factory",)

    factory: ISettlementFactory
    """The factory used to create new settlement from definitions."""

    def __init__(self, factory: ISettlementFactory) -> None:
        super().__init__()
        self.factory = factory


class ICharacterFactory(ABC):
    """Creates instances of character gameobjects using a single definition."""

    @abstractmethod
    def create_character(self, world: World, definition_id: str) -> GameObject:
        """Create instance of character from a character definition.

        Parameters
        ----------
        world
            The simulation's World instance.
        definition_id
            The ID of the character's definition.

        Returns
        -------
        GameObject
            The new character.
        """
        raise NotImplementedError()


class IChildFactory(ABC):
    """Creates instances of children given two parents."""

    @abstractmethod
    def create_child(
        self, birthing_parent: GameObject, other_parent: GameObject
    ) -> GameObject:
        """Create instance of a child from two parents.

        Parameters
        ----------
        birthing_parent
            The parent who gave birth to the child.
        other_parent
            The other parent contributing genetics to the child.

        Returns
        -------
        GameObject
            The new child.
        """
        raise NotImplementedError()


class CharacterLibrary(ContentDefinitionLibrary[CharacterDef]):
    """A collection of all character definitions."""

    _slots__ = ("factory", "child_factory")

    factory: ICharacterFactory
    """The factory used to create new characters from definitions."""
    child_factory: IChildFactory
    """The factory used to create new children from existing characters."""

    def __init__(
        self, factory: ICharacterFactory, child_factory: IChildFactory
    ) -> None:
        super().__init__()
        self.factory = factory
        self.child_factory = child_factory


class JobRoleLibrary(ContentDefinitionLibrary[JobRoleDef]):
    """Manages job role definitions and instances."""

    _slots__ = ("instances",)

    instances: dict[str, JobRole]
    """Job role instances."""

    def __init__(self) -> None:
        super().__init__()
        self.instances = {}

    def add_role(self, role: JobRole) -> None:
        """Add job role to the library."""
        self.instances[role.definition_id] = role

    def get_role(self, definition_id: str) -> JobRole:
        """Get a job role instance."""
        return self.instances[definition_id]


class IBusinessFactory(ABC):
    """Creates instances of business gameobjects using a single definition."""

    @abstractmethod
    def create_business(self, world: World, definition_id: str) -> GameObject:
        """Create instance of business from a business definition.

        Parameters
        ----------
        world
            The simulation's World instance.
        definition_id
            The ID of the business's definition.

        Returns
        -------
        GameObject
            The new business.
        """
        raise NotImplementedError()


class BusinessLibrary(ContentDefinitionLibrary[BusinessDef]):
    """A collection of all business definitions."""

    _slots__ = ("factory",)

    factory: IBusinessFactory
    """The factory used to create new business from definitions."""

    def __init__(self, factory: IBusinessFactory) -> None:
        super().__init__()
        self.factory = factory


class BeliefLibrary(ContentDefinitionLibrary[BeliefDef]):
    """The collection of all potential agent beliefs."""

    __slots__ = ("beliefs", "global_beliefs")

    beliefs: dict[str, Belief]
    """All potential beliefs."""
    global_beliefs: OrderedSet[str]
    """IDs of all beliefs that are held globally by all characters."""

    def __init__(self) -> None:
        super().__init__()
        self.beliefs = {}
        self.global_beliefs = OrderedSet([])

    def add_belief(self, belief: Belief) -> None:
        """Add a belief to the library."""

        self.beliefs[belief.belief_id] = belief

        if belief.is_global:
            self.global_beliefs.add(belief.belief_id)

    def get_belief(self, belief_id: str) -> Belief:
        """Get a belief from the library using its ID."""

        return self.beliefs[belief_id]


class LocationPreferenceLibrary(ContentDefinitionLibrary[LocationPreferenceDef]):
    """The collection of location preference rules."""

    __slots__ = ("rules",)

    rules: dict[str, LocationPreferenceRule]
    """Rules added to the location preferences."""

    def __init__(self) -> None:
        super().__init__()
        self.rules = {}

    def add_rule(self, rule: LocationPreferenceRule) -> None:
        """Add a location preference rule."""
        self.rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> LocationPreferenceRule:
        """Get a location preference rule."""

        return self.rules[rule_id]


class ICharacterNameFactory(Protocol):
    """Generates a character name."""

    @abstractmethod
    def __call__(self, world: World) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class CharacterNameFactories:
    """A Collection of factories that generate character names."""

    __slots__ = ("_factories",)

    _factories: dict[str, tuple[ICharacterNameFactory, list[str]]]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self._factories = {}

    def add_factory(
        self,
        name: str,
        factory: ICharacterNameFactory,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Add a factory."""
        self._factories[name] = (factory, tags if tags else [])

    def get_factory(self, name: str) -> ICharacterNameFactory:
        """Get a factory by name."""
        return self._factories[name][0]

    def get_with_tags(self, tags: list[str]) -> list[ICharacterNameFactory]:
        """Get a factory by name."""
        return get_with_tags(options=self._factories.values(), tags=tags)


class IBusinessNameFactory(Protocol):
    """Generates business names."""

    @abstractmethod
    def __call__(self, world: World) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class BusinessNameFactories:
    """A collection of factories that generate business names."""

    __slots__ = ("_factories",)

    _factories: dict[str, tuple[IBusinessNameFactory, list[str]]]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self._factories = {}

    def add_factory(
        self, name: str, factory: IBusinessNameFactory, tags: Optional[list[str]] = None
    ) -> None:
        """Add a factory."""
        self._factories[name] = (factory, tags if tags else [])

    def get_factory(self, name: str) -> IBusinessNameFactory:
        """Get a factory by name."""
        return self._factories[name][0]

    def get_with_tags(self, tags: list[str]) -> list[IBusinessNameFactory]:
        """Get a factory by name."""
        return get_with_tags(options=self._factories.values(), tags=tags)


class IDistrictNameFactory(Protocol):
    """Generates district names."""

    @abstractmethod
    def __call__(self, world: World) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class DistrictNameFactories:
    """A collection of factories that generate district names."""

    __slots__ = ("factories",)

    factories: dict[str, IDistrictNameFactory]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self.factories = {}

    def add_factory(self, name: str, factory: IDistrictNameFactory) -> None:
        """Add a factory."""
        self.factories[name] = factory

    def get_factory(self, name: str) -> IDistrictNameFactory:
        """Get a factory by name."""
        return self.factories[name]


class ISettlementNameFactory(Protocol):
    """Generates settlement names."""

    @abstractmethod
    def __call__(self, world: World) -> str:
        """Generate a new name."""
        raise NotImplementedError()


class SettlementNameFactories:
    """A collection of factories that generate settlement names."""

    __slots__ = ("_factories",)

    _factories: dict[str, tuple[ISettlementNameFactory, list[str]]]
    """Factories indexed by name."""

    def __init__(self) -> None:
        self._factories = {}

    def add_factory(
        self,
        name: str,
        factory: ISettlementNameFactory,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Add a factory."""
        self._factories[name] = (factory, tags if tags else [])

    def get_factory(self, name: str) -> ISettlementNameFactory:
        """Get a factory by name."""
        return self._factories[name][0]

    def get_with_tags(self, tags: list[str]) -> list[ISettlementNameFactory]:
        """Get a factory by name."""
        return get_with_tags(options=self._factories.values(), tags=tags)


class ActionConsiderationLibrary:
    """Manages all considerations that calculate the probability of a potential action.

    All considerations are grouped by action ID. End-users are responsible for casting
    the action instance if they care about type hints and such.
    """

    __slots__ = ("success_considerations",)

    success_considerations: defaultdict[str, OrderedSet[ActionConsideration]]
    """Considerations for calculating success probabilities."""

    def __init__(self) -> None:
        self.success_considerations = defaultdict(OrderedSet)

    def add_success_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Add a success consideration to the library."""
        self.success_considerations[action_id].add(consideration)

    def remove_success_consideration(
        self, action_id: str, consideration: ActionConsideration
    ) -> None:
        """Remove a success consideration from the library."""
        self.success_considerations[action_id].remove(consideration)

    def remove_all_success_considerations(self, action_id: str) -> None:
        """Add a success consideration to the library."""
        del self.success_considerations[action_id]

    def get_success_considerations(
        self, action_id: str
    ) -> Iterable[ActionConsideration]:
        """Get all success considerations for an action."""
        return self.success_considerations[action_id]


class PreconditionLibrary:
    """Manages effect precondition types and constructs them when needed."""

    _slots__ = "_precondition_types"

    _precondition_types: dict[str, Type[Precondition]]
    """Precondition types for loading data from config files."""

    def __init__(self) -> None:
        self._precondition_types = {}

    def get_precondition_type(self, precondition_name: str) -> Type[Precondition]:
        """Get a definition type."""
        return self._precondition_types[precondition_name]

    def add_precondition_type(self, precondition_type: Type[Precondition]) -> None:
        """Add a definition type for loading objs."""
        self._precondition_types[precondition_type.precondition_name()] = (
            precondition_type
        )

    def create_from_obj(self, world: World, obj: dict[str, Any]) -> Precondition:
        """Parse a definition from a dict and add to the library."""
        params = {**obj}
        precondition_name: str = params["type"]
        del params["type"]

        precondition_type = self.get_precondition_type(precondition_name)
        precondition = precondition_type.instantiate(world, params)

        return precondition


class EffectLibrary:
    """Manages effect types and constructs them when needed."""

    _slots__ = "_effect_types"

    _effect_types: dict[str, Type[Effect]]
    """SettlementDef types for loading data from config files."""

    def __init__(self) -> None:
        self._effect_types = {}

    def get_effect_type(self, effect_name: str) -> Type[Effect]:
        """Get a definition type."""
        return self._effect_types[effect_name]

    def add_effect_type(self, effect_type: Type[Effect]) -> None:
        """Add a definition type for loading objs."""
        self._effect_types[effect_type.effect_name()] = effect_type

    def create_from_obj(self, world: World, obj: dict[str, Any]) -> Effect:
        """Parse a definition from a dict and add to the library."""
        params = {**obj}
        effect_name: str = params["type"]
        del params["type"]

        effect_type = self.get_effect_type(effect_name)
        effect = effect_type.instantiate(world, params)

        return effect
