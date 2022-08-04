from __future__ import annotations

from typing import Any, Dict, Type, List

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, World, EntityArchetype
from neighborly.core.location import Location
from neighborly.core.position import Position2D


class Residence(Component):
    """Residence is a place where characters live"""

    __slots__ = "owners", "former_owners", "residents", "former_residents", "_vacant"

    def __init__(self) -> None:
        super().__init__()
        self.owners: OrderedSet[int] = OrderedSet([])
        self.former_owners: OrderedSet[int] = OrderedSet([])
        self.residents: OrderedSet[int] = OrderedSet([])
        self.former_residents: OrderedSet[int] = OrderedSet([])
        self._vacant: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "owners": list(self.owners),
            "former_owners": list(self.former_owners),
            "residents": list(self.residents),
            "former_residents": list(self.former_residents),
            "vacant": self._vacant,
        }

    def add_owner(self, owner: int) -> None:
        """Add owner to the residence"""
        self.owners.add(owner)

    def remove_owner(self, owner: int) -> None:
        """Remove owner from residence"""
        self.owners.remove(owner)

    def is_owner(self, character: int) -> bool:
        """Return True if the character is an owner of this residence"""
        return character in self.owners

    def add_resident(self, resident: int) -> None:
        """Add a tenant to this residence"""
        self.residents.add(resident)
        self._vacant = False

    def remove_resident(self, resident: int) -> None:
        """Remove a tenant rom this residence"""
        self.residents.remove(resident)
        self.former_residents.add(resident)
        self._vacant = len(self.residents) == 0

    def is_resident(self, character: int) -> bool:
        """Return True if the given character is a resident"""
        return character in self.residents

    def is_vacant(self) -> bool:
        """Return True if the residence is vacant"""
        return self._vacant

    @classmethod
    def create(cls, world: World, **kwargs) -> Residence:
        return cls()


class Resident(Component):
    """Component attached to characters indicating that they live in the town"""

    __slots__ = "residence"

    def __init__(self, residence: int) -> None:
        super().__init__()
        self.residence: int = residence

    def on_remove(self) -> None:
        world = self.gameobject.world
        residence = world.get_gameobject(self.residence).get_component(Residence)
        residence.remove_resident(self.gameobject.id)
        if residence.is_owner(self.gameobject.id):
            residence.remove_owner(self.gameobject.id)


class ResidenceArchetype(EntityArchetype):
    __slots__ = "spawn_multiplier",

    def __init__(
        self,
        name: str,
        spawn_multiplier: int = 1,
        extra_components: Dict[Type[Component], Dict[str, Any]] = None
    ) -> None:
        super().__init__(name)
        self.spawn_multiplier: int = spawn_multiplier

        self.add(Residence)
        self.add(Location)
        self.add(Position2D)

        if extra_components:
            for component_type, params in extra_components.items():
                self.add(component_type, **params)


class ResidenceArchetypeLibrary:
    _registry: Dict[str, ResidenceArchetype] = {}

    @classmethod
    def register(cls, archetype: ResidenceArchetype, name: str = None, ) -> None:
        """Register a new LifeEventType mapped to a name"""
        cls._registry[name if name else archetype.name] = archetype

    @classmethod
    def get_all(cls) -> List[ResidenceArchetype]:
        return list(cls._registry.values())

    @classmethod
    def get(cls, name: str) -> ResidenceArchetype:
        """Get a LifeEventType using a name"""
        return cls._registry[name]
