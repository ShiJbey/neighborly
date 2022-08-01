from __future__ import annotations

from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, Event, IEventListener, World


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


class Resident(Component, IEventListener):
    """Component attached to characters indicating that they live in the town"""

    __slots__ = "residence"

    def __init__(self, residence: int) -> None:
        super().__init__()
        self.residence: int = residence

    @classmethod
    def create(cls, world, **kwargs) -> Component:
        return Resident(**kwargs)

    def will_handle_event(self, event: Event) -> bool:
        return True

    def handle_event(self, event: Event) -> bool:
        event_type = event.get_type()
        if event_type == "death":
            print("Character died and now we remove them from the house.")
            # Remove the resident from the residence
            world = self.gameobject.world
            residence = world.get_gameobject(self.residence).get_component(Residence)
            residence.remove_resident(self.gameobject.id)
            if residence.is_owner(self.gameobject.id):
                residence.remove_owner(self.gameobject.id)
        return True
