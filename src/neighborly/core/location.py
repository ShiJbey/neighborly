from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import Component


class Location(Component):
    """Anywhere where game characters may be"""

    __slots__ = "entities"

    def __init__(self) -> None:
        super().__init__()
        self.entities: OrderedSet[int] = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "entities": list(self.entities),
        }

    def add_entity(self, entity: int) -> None:
        self.entities.append(entity)

    def remove_entity(self, entity: int) -> None:
        self.entities.remove(entity)

    def has_entity(self, entity: int) -> bool:
        return entity in self.entities

    def __repr__(self) -> str:
        return "{}(entities={})".format(
            self.__class__.__name__,
            self.entities,
        )
