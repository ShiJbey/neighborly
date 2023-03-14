from __future__ import annotations

import dataclasses
from typing import Dict, Iterator, List, Type

from neighborly.components.business import OccupationType
from neighborly.core.life_event import ActionableLifeEvent
from neighborly.core.location_bias import ILocationBiasRule
from neighborly.core.social_rule import ISocialRule


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
