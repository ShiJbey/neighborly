"""neighborly.settlement

This module contains classes and helper functions for defining and modeling settlements.

"""

from __future__ import annotations

from typing import Any

from neighborly.ecs import Component, GameObject


class District(Component):
    """A subsection of a settlement."""

    __slots__ = ("name", "businesses", "business_capacity")

    name: str
    """The district's name."""
    businesses: list[GameObject]
    """businesses within this district."""
    business_capacity: int
    """The maximum number of businesses that this district can support."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.businesses = []
        self.business_capacity = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "businesses": [l.uid for l in self.businesses],
            "business_capacity": self.business_capacity,
        }


class Settlement(Component):
    """A town, city, or village where characters live."""

    __slots__ = ("name", "population", "districts")

    name: str
    """The settlement's name."""
    population: int
    """The number of characters living in this district."""
    districts: list[GameObject]
    """References to districts within this settlement."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.districts = []
        self.population = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "districts": [d.uid for d in self.districts],
            "population": self.population,
        }
