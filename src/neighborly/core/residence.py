from ordered_set import OrderedSet

from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


class Residence(Component):
    __slots__ = 'owners', 'former_owners', 'residents', 'former_residents', '_vacant'

    def __init__(self) -> None:
        super().__init__()
        self.owners: OrderedSet[int] = OrderedSet()
        self.former_owners: OrderedSet[int] = OrderedSet()
        self.residents: OrderedSet[int] = OrderedSet()
        self.former_residents: OrderedSet[int] = OrderedSet()
        self._vacant: bool = True

    def add_tenant(self, person: int, is_owner: bool = False) -> None:
        """Add a tenant to this residence"""
        self.residents.add(person)
        if is_owner:
            self.owners.add(person)
        self._vacant = False

    def remove_tenant(self, person: int) -> None:
        """Remove a tenant rom this residence"""
        self.residents.remove(person)
        self.former_residents.add(person)
        if person in self.owners:
            self.owners.remove(person)
            self.former_owners.add(person)
        self._vacant = len(self.residents) == 0

    def is_vacant(self) -> bool:
        return self._vacant


class ResidenceFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Residence")

    def create(self, spec: ComponentSpec, **kwargs) -> Residence:
        return Residence()
