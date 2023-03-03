from __future__ import annotations

import dataclasses
import random
import re
from typing import Any, Dict, Iterator, List, Optional, Protocol, Type

from neighborly.components.activity import Activity
from neighborly.components.business import OccupationType, Service
from neighborly.core.ai.brain import IAIBrain
from neighborly.core.ecs import GameObject, World
from neighborly.core.life_event import ActionableLifeEvent
from neighborly.core.location_bias import ILocationBiasRule
from neighborly.core.settlement import Settlement
from neighborly.core.social_rule import ISocialRule
from neighborly.core.time import SimDateTime
from neighborly.prefabs import BusinessPrefab, CharacterPrefab, ResidencePrefab


class ActivityLibrary:
    """
    Repository of all the various activities that can exist in the simulated world

    Notes
    -----
    This classes uses the flyweight design pattern to save memory since many activities
    are shared between location instances. Also, it makes activity comparisons faster
    by mapping activity names to integers and comparing those values instead of the
    name strings.
    """

    __slots__ = "_activities", "_name_to_id"

    def __init__(self, activities: Optional[List[str]] = None) -> None:
        self._activities: List[Activity] = []
        self._name_to_id: Dict[str, int] = {}

        if activities:
            for activity_name in activities:
                self.get(activity_name)

    def get(self, activity_name: str) -> Activity:
        """Get an Activity instance

        Parameters
        ----------
        activity_name: str
            A name of an activity

        Returns
        -------
        Activity
            The activity instance with the given activity name
        """
        lc_activity_name = activity_name.lower()

        if lc_activity_name in self._name_to_id:
            return self._activities[self._name_to_id[lc_activity_name]]

        activity_id = len(self._activities)
        activity = Activity(activity_id, lc_activity_name)
        self._activities.append(activity)
        self._name_to_id[lc_activity_name] = activity_id

        return activity

    def __contains__(self, activity_name: str) -> bool:
        """Return True if a service type exists with the given name"""
        return activity_name.lower() in self._name_to_id

    def __iter__(self) -> Iterator[Activity]:
        """Return iterator for the ActivityLibrary"""
        return self._activities.__iter__()

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, str([str(a) for a in self._activities])
        )


class ServiceLibrary:
    """
    Repository of various services offered by a business

    Attributes
    ----------
    _next_id: int
        The next ID assigned to a new ServiceType instance
    _services: List[Service]
        A list of all the possible services a business could have
    _name_to_id: Dict[str, int]
        Mapping of service names to indexes into the _services list
    """

    __slots__ = "_next_id", "_services", "_name_to_id"

    def __init__(self) -> None:
        self._next_id: int = 0
        self._services: List[Service] = []
        self._name_to_id: Dict[str, int] = {}

    def __contains__(self, service_name: str) -> bool:
        """Return True if a service type exists with the given name"""
        return service_name.lower() in self._name_to_id

    def get(self, service_name: str) -> Service:
        lc_service_name = service_name.lower()

        if lc_service_name in self._name_to_id:
            return self._services[self._name_to_id[lc_service_name]]

        uid = self._next_id
        self._next_id += 1
        service_type = Service(uid, lc_service_name)
        self._services.append(service_type)
        self._name_to_id[lc_service_name] = uid
        return service_type


class OccupationTypeLibrary:
    """Collection OccupationType information for lookup at runtime"""

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, OccupationType] = {}

    def add(
        self,
        occupation_type: OccupationType,
    ) -> None:
        """
        Add a new occupation type to the library

        Parameters
        ----------
        occupation_type: OccupationType
            The occupation type instance to add
        """
        self._registry[occupation_type.name] = occupation_type

    def get(self, name: str) -> OccupationType:
        """
        Get an OccupationType by name

        Parameters
        ----------
        name: str
            The registered name of the OccupationType

        Returns
        -------
        OccupationType

        Raises
        ------
        KeyError
            When there is not an OccupationType
            registered to that name
        """
        return self._registry[name]


class BusinessLibrary:
    """Collection Business prefabs"""

    __slots__ = "_prefabs"

    def __init__(self) -> None:
        self._prefabs: Dict[str, BusinessPrefab] = {}

    def iter_prefabs(self) -> Iterator[BusinessPrefab]:
        """Iterate the prefabs in the library"""
        return self._prefabs.values().__iter__()

    def add(self, prefab: BusinessPrefab) -> None:
        """Add a new prefab

        Parameters
        ----------
        prefab: BusinessPrefab
            The prefab to add
        """
        self._prefabs[prefab.name] = prefab

    def get_all(self) -> List[BusinessPrefab]:
        """Get all stored prefabs"""
        return list(self._prefabs.values())

    def get(self, name: str) -> BusinessPrefab:
        """Get a prefab by name"""
        return self._prefabs[name]

    def get_matching_prefabs(self, *name_patterns: str) -> List[BusinessPrefab]:
        """Get all component bundles that match the given regex strings"""

        matches: List[BusinessPrefab] = []

        for name, prefab in self._prefabs.items():
            if any([re.match(pattern, name) for pattern in name_patterns]):
                matches.append(prefab)

        return matches

    def get_eligible(self, settlement: GameObject) -> List[BusinessPrefab]:
        """Get all business prefabs that can be built in the given settlement"""
        world = settlement.world
        settlement_comp = settlement.get_component(Settlement)
        date = world.get_resource(SimDateTime)

        matches: List[BusinessPrefab] = []

        for _, prefab in self._prefabs.items():
            if (
                settlement_comp.business_counts[prefab.name] < prefab.max_instances
                and settlement_comp.population >= prefab.min_population
                and (prefab.year_available <= date.year < prefab.year_obsolete)
                and not prefab.is_template
            ):
                matches.append(prefab)

        return matches

    def choose_random(
        self, world: World, settlement: GameObject
    ) -> Optional[BusinessPrefab]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """
        settlement_comp = settlement.get_component(Settlement)
        date = world.get_resource(SimDateTime)
        rng = world.get_resource(random.Random)

        choices: List[BusinessPrefab] = []
        weights: List[int] = []

        for prefab in self.get_all():
            if (
                settlement_comp.business_counts[prefab.name] < prefab.max_instances
                and settlement_comp.population >= prefab.min_population
                and (prefab.year_available <= date.year < prefab.year_obsolete)
                and not prefab.is_template
            ):
                choices.append(prefab)
                weights.append(prefab.spawn_frequency)

        if choices:
            # Choose an archetype at random
            return rng.choices(population=choices, weights=weights, k=1)[0]

        return None


class CharacterLibrary:
    """Collection of factories that create character entities"""

    __slots__ = "_prefabs"

    def __init__(self) -> None:
        self._prefabs: Dict[str, CharacterPrefab] = {}

    def add(self, prefab: CharacterPrefab) -> None:
        """Register a new prefab"""
        self._prefabs[prefab.name] = prefab

    def get_all(self) -> List[CharacterPrefab]:
        """Get all stored archetypes"""
        return list(self._prefabs.values())

    def get(self, name: str) -> CharacterPrefab:
        """Get a prefab by name"""
        return self._prefabs[name]

    def get_matching_prefabs(self, *name_patterns: str) -> List[CharacterPrefab]:
        """Get all component bundles that match the given regex strings"""

        matches: List[CharacterPrefab] = []

        for name, bundle in self._prefabs.items():
            if any([re.match(pattern, name) for pattern in name_patterns]):
                matches.append(bundle)

        return matches

    def choose_random(
        self,
        rng: random.Random,
    ) -> Optional[CharacterPrefab]:
        """Performs a weighted random selection across all character archetypes"""
        choices: List[CharacterPrefab] = []
        weights: List[int] = []

        for prefab in self.get_all():
            if prefab.is_template is False:
                choices.append(prefab)
                weights.append(prefab.spawn_frequency)

        if choices:
            # Choose an archetype at random
            return rng.choices(population=choices, weights=weights, k=1)[0]

        return None

    def __len__(self) -> int:
        return len(self._prefabs)


class ResidenceLibrary:
    """Collection factories that create residence entities"""

    __slots__ = "_prefabs"

    def __init__(self) -> None:
        self._prefabs: Dict[str, ResidencePrefab] = {}

    def add(self, prefab: ResidencePrefab) -> None:
        """Register a new prefab"""
        self._prefabs[prefab.name] = prefab

    def get_all(self) -> List[ResidencePrefab]:
        """Get all stored archetypes"""
        return list(self._prefabs.values())

    def get(self, name: str) -> ResidencePrefab:
        """Get a prefab by name"""
        return self._prefabs[name]

    def get_matching_prefabs(self, *name_patterns: str) -> List[ResidencePrefab]:
        """Get all component bundles that match the given regex strings"""

        matches: List[ResidencePrefab] = []

        for name, bundle in self._prefabs.items():
            if any([re.match(pattern, name) for pattern in name_patterns]):
                matches.append(bundle)

        return matches

    def choose_random(
        self,
        rng: random.Random,
    ) -> Optional[ResidencePrefab]:
        """Performs a weighted random selection across all character archetypes"""
        choices: List[ResidencePrefab] = []
        weights: List[int] = []

        for prefab in self.get_all():
            if prefab.is_template is False:
                choices.append(prefab)
                weights.append(prefab.spawn_frequency)

        if choices:
            return rng.choices(population=choices, weights=weights, k=1)[0]

        return None

    def __len__(self) -> int:
        return len(self._prefabs)

    def __bool__(self) -> bool:
        return bool(self._prefabs)


class LifeEventLibrary:
    """
    Static class used to store instances of LifeEventTypes for
    use at runtime.
    """

    __slots__ = "_registry"

    def __init__(self) -> None:
        self._registry: Dict[str, Type[ActionableLifeEvent]] = {}

    def add(self, life_event_type: Type[ActionableLifeEvent]) -> None:
        """Register a new LifeEventType mapped to a name"""
        self._registry[life_event_type.__name__] = life_event_type

    def get_all(self) -> List[Type[ActionableLifeEvent]]:
        """Get all LifeEventTypes stores in the Library"""
        return list(self._registry.values())


@dataclasses.dataclass(frozen=True)
class SocialRuleInfo:
    rule: ISocialRule
    description: str = ""


class SocialRuleLibrary:
    """Repository of ISocialRule instances to use during the simulation."""

    __slots__ = "_rules"

    def __init__(self) -> None:
        self._rules: List[SocialRuleInfo] = []

    def add(self, rule: ISocialRule, description: str = "") -> None:
        self._rules.append(SocialRuleInfo(rule, description))

    def __iter__(self) -> Iterator[SocialRuleInfo]:
        return self._rules.__iter__()


@dataclasses.dataclass(frozen=True)
class LocationBiasRuleInfo:
    rule: ILocationBiasRule
    description: str = ""


class LocationBiasRuleLibrary:
    """Repository of active rules that determine what location characters frequent"""

    __slots__ = "_rules"

    def __init__(self) -> None:
        self._rules: List[LocationBiasRuleInfo] = []

    def add(self, rule: ILocationBiasRule, description: str = "") -> None:
        self._rules.append(LocationBiasRuleInfo(rule, description))

    def __iter__(self) -> Iterator[LocationBiasRuleInfo]:
        return self._rules.__iter__()


class AIBrainFactory(Protocol):
    def __call__(self, **kwargs: Any) -> IAIBrain:
        """Create IAIBrain instance"""
        raise NotImplementedError


class AIBrainLibrary:
    """Collection of factory callables that produce IAIBrain instances

    This library maps string names to callable instances that instantiate IAIBrains that
    will be encapsulated inside AIComponents
    """

    __slots__ = "_brains"

    def __init__(self) -> None:
        self._brains: Dict[str, AIBrainFactory] = {}

    def add(self, name: str, factory: AIBrainFactory) -> None:
        """Add a brain instance to the library

        Parameters
        ----------
        name: str
            The name to map the brain to
        factory: AIBrainFactory
            Factory callable that creates brain instances
        """
        self._brains[name] = factory

    def __getitem__(self, item: str) -> AIBrainFactory:
        return self._brains[item]
