"""Location preference rules.

This module provides interface and classes that help characters determine
where within a settlement they choose to frequent.

"""
from __future__ import annotations

import dataclasses
from typing import Iterator, Optional, Protocol

from ordered_set import OrderedSet

from neighborly.ecs import GameObject


class ILocationPreferenceRule(Protocol):
    """Define what locations characters are likely to frequent."""

    def __call__(self, character: GameObject, location: GameObject) -> Optional[float]:
        """
        Calculate a weight modifier for a character frequenting a location

        Parameters
        ----------
        character
            The character to check
        location
            The location to check

        Returns
        -------
        float or None
            Optionally returns a float value representing a weight modifier for
            how likely the given character would be to frequent the given location
            based on some precondition(s)
        """
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class LocationPreferenceRuleInfo:
    """Information about a location preference rule."""

    rule: ILocationPreferenceRule
    """The callable function that implements the rule"""

    description: str = ""
    """A text description of the rule"""


class LocationPreferenceRuleLibrary:
    """Repository of active rules that determine what location characters frequent."""

    __slots__ = "_rules"

    _rules: OrderedSet[LocationPreferenceRuleInfo]
    """All registered rules."""

    def __init__(self) -> None:
        self._rules = OrderedSet([])

    def add(self, rule: ILocationPreferenceRule, description: str = "") -> None:
        self._rules.append(LocationPreferenceRuleInfo(rule, description))

    def iter_rules(self) -> Iterator[LocationPreferenceRuleInfo]:
        return self._rules.__iter__()
