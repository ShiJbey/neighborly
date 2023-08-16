"""Settlement.

The module contains Neighborly's settlement implementation. Settlements can represent
towns, cities, villages, etc. There is only one settlement per simulation, and it is
stored as a shared resource in the ECS resource manager.

"""

from __future__ import annotations

from typing import Any, Dict

from neighborly.ecs import ISerializable


class Settlement(ISerializable):
    """A place where characters live, go to work, and interact."""

    __slots__ = "name", "population"

    name: str
    """The name of the settlement"""

    population: int
    """The number of characters who are residents of the settlement."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.population = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "population": self.population}

    def __str__(self) -> str:
        return f"{self.name}(Pop. {self.population})"

    def __repr__(self) -> str:
        return f"Settlement(name={self.name}, population={self.population})"
