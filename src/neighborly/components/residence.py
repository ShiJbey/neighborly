"""Components for residence GameObjects and tracking residential status.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Optional, Type, TypedDict, final

from ordered_set import OrderedSet

from neighborly.ecs import Component, Event, GameObject, ISerializable, World
from neighborly.events import ChangeResidenceEvent
from neighborly.settlement import Settlement
from neighborly.spawn_table import ResidenceSpawnTable, ResidenceSpawnTableEntry
from neighborly.statuses import IStatus
from neighborly.time import SimDateTime


class Residence(Component, ISerializable):
    """A Residence is a place where characters live."""

    __slots__ = ("owners", "residents", "residence_type")

    owners: OrderedSet[GameObject]
    """Characters that currently own the residence."""

    residents: OrderedSet[GameObject]
    """All the characters who live at the residence (including non-owners)."""

    residence_type: ResidenceType
    """Reference to the ResidenceType component."""

    def __init__(self, residence_type: ResidenceType) -> None:
        super().__init__()
        self.owners = OrderedSet([])
        self.residents = OrderedSet([])
        self.residence_type = residence_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owners": [entry.uid for entry in self.owners],
            "residents": [entry.uid for entry in self.residents],
        }

    def add_owner(self, owner: GameObject) -> None:
        """Add owner to the residence.

        Parameters
        ----------
        owner
            A GameObject reference to a residence owner.
        """
        self.owners.add(owner)

    def remove_owner(self, owner: GameObject) -> None:
        """Remove owner from residence.

        Parameters
        ----------
        owner
            A GameObject reference to a residence owner.
        """
        self.owners.remove(owner)

    def is_owner(self, character: GameObject) -> bool:
        """Check if a GameObject owns a residence.

        Parameters
        ----------
        character
            A GameObject reference to a residence owner.
        """
        return character in self.owners

    def add_resident(self, resident: GameObject) -> None:
        """Add a tenant to this residence.

        Parameters
        ----------
        resident
            A GameObject reference to a resident.
        """
        self.residents.add(resident)

    def remove_resident(self, resident: GameObject) -> None:
        """Remove a tenant rom this residence.

        Parameters
        ----------
        resident
            A GameObject reference to a resident.
        """
        self.residents.remove(resident)

    def is_resident(self, character: GameObject) -> bool:
        """Check if a GameObject is a resident.

        Parameters
        ----------
        character
            A GameObject reference to a character
        """
        return character in self.residents

    def __repr__(self) -> str:
        return f"Residence({self.to_dict()})"

    def __str__(self) -> str:
        return f"Residence({self.to_dict()})"


class Resident(IStatus):
    """A Component attached to characters that tracks where they live."""

    __slots__ = "residence"

    residence: GameObject
    """The GameObject ID of their residence."""

    def __init__(self, year_created: int, residence: GameObject) -> None:
        """
        Parameters
        ----------
        year_created
            The year the character became a resident.
        residence
            A GameObject reference to their residence.
        """
        super().__init__(year_created)
        self.residence = residence

    def on_deactivate(self) -> None:
        set_residence(self.gameobject, None)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "residence": self.residence.uid}

    def __repr__(self) -> str:
        return f"Resident({self.to_dict()})"

    def __str__(self) -> str:
        return f"Resident({self.to_dict()})"


class Vacant(IStatus):
    """Tags a residence that does not currently have anyone living there."""

    pass


class ResidenceConfig(TypedDict):
    spawn_frequency: int


class ResidenceType(Component, ABC):
    config: ClassVar[ResidenceConfig] = {"spawn_frequency": 1}

    @classmethod
    def on_register(cls, world: World) -> None:
        world.resource_manager.get_resource(ResidenceSpawnTable).update(
            ResidenceSpawnTableEntry(
                name=cls.__name__, spawn_frequency=cls.config["spawn_frequency"]
            )
        )

    @classmethod
    @abstractmethod
    def _instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        """Create new residence instance.

        Parameters
        ----------
        world
            The world instance to spawn into.
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        GameObject
            The residence instance.
        """
        return world.gameobject_manager.spawn_gameobject()

    @classmethod
    @final
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        """Create a new GameObject instance of the given residence type.

        Parameters
        ----------
        world
            The world to spawn the residence into
        **kwargs
            Keyword arguments to pass to the ResidenceType's factory

        Returns
        -------
        GameObject
            the instantiated character
        """
        residence = cls._instantiate(world, **kwargs)

        ResidenceCreatedEvent(world, residence).dispatch()

        return residence


class BaseResidence(ResidenceType, ABC):
    @classmethod
    def _instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        residence = world.gameobject_manager.spawn_gameobject()

        residence.name = f"{cls.__name__}({residence.uid})"

        residence_type = residence.add_component(cls)

        residence.add_component(Residence, residence_type=residence_type)

        return residence


class ResidenceCreatedEvent(Event):
    __slots__ = "_residence"

    _residence: GameObject
    """Reference to the created residence."""

    def __init__(
        self,
        world: World,
        residence: GameObject,
    ) -> None:
        super().__init__(world)
        self._residence = residence

    @property
    def residence(self) -> GameObject:
        return self._residence


def set_residence(
    character: GameObject,
    new_residence: Optional[GameObject],
    is_owner: bool = False,
) -> None:
    """Sets the characters current residence.

    Parameters
    ----------
    character
        The character to move
    new_residence
        An optional residence to move them to. If None is given and the character
        has a current residence, they are removed from their current residence
    is_owner
        Should the character be listed one of the owners of the new residence
    """
    current_date = character.world.resource_manager.get_resource(SimDateTime)
    settlement = character.world.resource_manager.get_resource(Settlement)
    former_residence: Optional[GameObject] = None

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = resident.residence
        former_residence_comp = former_residence.get_component(Residence)

        if former_residence_comp.is_owner(character):
            former_residence_comp.remove_owner(character)

        former_residence_comp.remove_resident(character)
        character.remove_component(Resident)

        settlement.population -= 1

        if len(former_residence_comp.residents) <= 0:
            former_residence.add_component(Vacant, timestamp=current_date.year)

    # Don't add them to a new residence if none is given
    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(Residence).add_resident(character)

    if is_owner:
        new_residence.get_component(Residence).add_owner(character)

    character.add_component(
        Resident, residence=new_residence, year_created=current_date.year
    )

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)

    settlement.population += 1

    ChangeResidenceEvent(
        world=character.world,
        old_residence=former_residence,
        new_residence=new_residence,
        character=character,
        date=current_date.copy(),
    ).dispatch()
